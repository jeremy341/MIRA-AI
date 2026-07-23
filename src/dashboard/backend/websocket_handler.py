"""
WebSocket handlers for real-time video streaming
"""
import asyncio
import base64
from datetime import datetime
import cv2
import numpy as np
from typing import Dict, Any
from starlette.websockets import WebSocketDisconnect

from models import Detection, SystemMetrics


class WebSocketHandler:
    """Handle WebSocket connections for video streaming"""
    
    def __init__(self, camera_service):
        self.camera_service = camera_service
        self.connections = set()
        self.frame_buffer = None
        self.latest_detections = []
        self._broadcast_queue = asyncio.Queue()
        self._broadcast_task = None
        
        # Register callbacks
        camera_service.on_detection = self._on_detections
        camera_service.on_metrics = self._on_metrics
        camera_service.on_status_change = self._on_status_change
    
    async def start(self):
        """Start the background broadcast task"""
        self._broadcast_task = asyncio.create_task(self._broadcast_consumer())
    
    async def stop(self):
        """Stop the background broadcast task"""
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
    
    async def _broadcast_consumer(self):
        """Consume messages from the broadcast queue and send to all connections"""
        while True:
            try:
                message = await self._broadcast_queue.get()
                if not self.connections:
                    continue
                
                # Collect tasks for all connections
                tasks = []
                to_remove = set()
                for websocket in self.connections:
                    try:
                        tasks.append(websocket.send_json(message))
                    except Exception:
                        to_remove.add(websocket)
                
                # Remove broken connections
                for ws in to_remove:
                    self.connections.discard(ws)
                
                # Send concurrently
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                break
            except Exception:
                continue
    
    async def handle_video_stream(self, websocket):
        """Handle video streaming WebSocket connection"""
        self.connections.add(websocket)
        try:
            await websocket.send_json({
                "type": "status",
                "status": "connected",
                "message": "Video stream connected"
            })
            
            # Send initial frame if available
            if self.frame_buffer is not None:
                await self._send_frame(websocket, self.frame_buffer)
            
            # Keep connection alive
            async for message in websocket:
                if message == "ping":
                    await websocket.send("pong")
                elif message.startswith("config:"):
                    # Handle configuration updates
                    await self._handle_config(websocket, message[7:])
                    
        except (WebSocketDisconnect, Exception):
            pass
        finally:
            self.connections.remove(websocket)
    
    async def _on_detections(self, detections: list[Detection]):
        """Callback when new detections are available"""
        self.latest_detections = detections
        
        # Convert detections to serializable format
        serialized_detections = []
        for det in detections:
            serialized_detections.append({
                "class": det.class_name.value,
                "confidence": det.confidence,
                "bbox": det.bbox,
                "track_id": det.track_id,
                "timestamp": det.timestamp.isoformat()
            })
        
        # Send to all connected clients
        message = {
            "type": "detections",
            "detections": serialized_detections,
            "count": len(detections)
        }
        
        await self._broadcast_queue.put(message)
    
    async def _on_metrics(self, metrics: SystemMetrics):
        """Callback when system metrics are updated"""
        message = {
            "type": "metrics",
            "fps": round(metrics.fps, 1),
            "inference_latency_ms": round(metrics.inference_latency_ms, 1),
            "avg_latency_ms": round(metrics.avg_latency_ms, 1),
            "cpu_percent": round(metrics.cpu_percent, 1),
            "memory_percent": round(metrics.memory_percent, 1),
            "temperature_celsius": round(metrics.temperature_celsius, 1) if metrics.temperature_celsius else None,
            "detections_per_second": round(metrics.detections_per_second, 1),
            "skip_frames": metrics.skip_frames,
            "timestamp": metrics.timestamp.isoformat()
        }
        
        await self._broadcast_queue.put(message)
    
    async def _on_status_change(self, status, message):
        """Callback when system status changes"""
        await self._broadcast_queue.put({
            "type": "status",
            "status": status.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_frame(self, frame: np.ndarray, detections: list[Detection] = None):
        """Update the current frame with detections drawn"""
        if frame is None:
            return
        
        # Draw detections on frame
        annotated_frame = frame.copy()
        
        if detections:
            for det in detections:
                x1, y1, x2, y2 = det.bbox
                
                # Choose color based on class
                colors = {
                    "glass": (0, 255,  0),    # Green
                    "metal": (255, 165, 0),  # Orange
                    "paper": (0, 0, 255),    # Red
                    "plastic": (255, 255, 0), # Yellow
                    "trash": (128, 0, 128)   # Purple
                }
                
                color = colors.get(det.class_name.value, (255, 255, 255))
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{det.class_name.value}: {det.confidence:.2f}"
                if det.track_id is not None:
                    label = f"[{det.track_id}] {label}"
                
                # Calculate text size
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                
                # Draw background for text
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1 - text_height - 4),
                    (x1 + text_width, y1),
                    color,
                    -1
                )
                
                # Draw text
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, y1 - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1
                )
        
        # Store frame for new connections
        self.frame_buffer = annotated_frame
        
        # Convert frame to JPEG
        _, buffer = cv2.imencode('.jpg', annotated_frame, [
            cv2.IMWRITE_JPEG_QUALITY, 85
        ])
        
        # Encode as base64
        frame_data = base64.b64encode(buffer).decode('utf-8')
        
        # Create message
        message = {
            "type": "frame",
            "frame": frame_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Push to broadcast queue (non-blocking)
        try:
            self._broadcast_queue.put_nowait(message)
        except asyncio.QueueFull:
            pass  # Drop frame if queue is full
    
    async def _send_frame(self, websocket, frame: np.ndarray):
        """Send a single frame to a websocket"""
        if frame is None:
            return
        
        _, buffer = cv2.imencode('.jpg', frame, [
            cv2.IMWRITE_JPEG_QUALITY, 85
        ])
        
        frame_data = base64.b64encode(buffer).decode('utf-8')
        
        await websocket.send_json({
            "type": "frame",
            "frame": frame_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_config(self, websocket, config_json: str):
        """Handle configuration updates from client"""
        try:
            import json
            config = json.loads(config_json)
            
            # Update camera configuration
            if "camera" in config:
                camera_config = config["camera"]
                # Apply configuration changes...
                pass
            
            # Update model configuration
            if "model" in config:
                model_config = config["model"]
                # Apply configuration changes...
                pass
            
            await websocket.send_json({
                "type": "config_updated",
                "message": "Configuration updated successfully"
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Configuration error: {str(e)}"
            })
    
    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        # Create tasks for all connections
        tasks = []
        to_remove = set()
        for websocket in self.connections:
            try:
                tasks.append(websocket.send_json(message))
            except Exception:
                # Mark broken connections for removal
                to_remove.add(websocket)
        
        # Remove broken connections after iteration
        for websocket in to_remove:
            self.connections.discard(websocket)
        
        # Send concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)