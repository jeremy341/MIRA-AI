/**
 * English pages for the dashboard (version 1.1.0 and later): the overview, one page per area, the v1 API
 * reference and the help pages. German twin: de-dashboard.ts, same structure.
 *
 * Every route, limit and default below was checked against src/dashboard (backend routers and the UI source)
 * and docs/dashboard-v2/CONTRACT.md. Do not add a number or a field here without checking it there first.
 * No em dashes or en dashes in any text.
 */

import { code, lines, list, note, p, table, warning } from "./helpers";
import type { DocPage } from "./types";

export const dashboard: DocPage = {
  slug: "dashboard",
  title: "The dashboard",
  group: "dashboard",
  summary: "Start the local dashboard, see what each page does, and where its data is kept.",
  lead: "The dashboard is a local web app served by `mira dashboard`. It records detection runs as sessions, replays and exports them, compares models and keeps a short hardware history. Camera frames and detections stay on your computer.",
  sections: [
    {
      id: "start",
      title: "Start it",
      blocks: [
        code(lines("mira dashboard", "mira dashboard --port 8080", "mira dashboard --host 0.0.0.0")),
        p("The defaults are `--host 127.0.0.1` and `--port 8000`, so the page is at `http://127.0.0.1:8000`."),
        warning(
          "Binding to 0.0.0.0",
          "`--host 0.0.0.0` makes the dashboard reachable from your network. It has no login, and anyone who can reach it can start your camera. Keep the default unless you need remote access on a trusted network.",
        ),
        p(
          "The package from PyPI contains the built interface. In a source checkout the interface has to be built once (`corepack pnpm install` and `corepack pnpm build` in `src/dashboard/ui`); until then the server shows the previous single-file dashboard. That one is always available at `/legacy`, and `MIRA_DASHBOARD_UI=legacy` makes it the page at `/`.",
        ),
      ],
    },
    {
      id: "pages",
      title: "The five pages",
      blocks: [
        table(
          "Dashboard pages",
          ["Page", "What it does"],
          [
            ["[Detect](/docs/detect)", "Live detection from a camera, or one image file. Start and stop a session."],
            ["[Sessions](/docs/sessions)", "Every recorded run, with totals, a replayable timeline, export and import."],
            ["[Models](/docs/compare-benchmark)", "Compare two to four models on one image, or run a benchmark."],
            ["[Analytics](/docs/analytics)", "Charts for a session, the hardware history and the sorting arm log."],
            ["Settings", "Camera and model settings. They are locked while a stream runs."],
          ],
        ),
      ],
    },
    {
      id: "data",
      title: "Where the data lives",
      blocks: [
        p(
          "Everything is saved in one SQLite file: sessions, detections, metrics, hardware samples, jobs, comparisons, benchmark runs and arm events. Camera frames are not saved, only the detections (class, confidence, box and track id).",
        ),
        table(
          "Environment variables",
          ["Variable", "Default", "Effect"],
          [
            ["`MIRA_DASHBOARD_DB`", "`~/.mira/dashboard.db`", "Path of the SQLite file."],
            ["`MIRA_HARDWARE_INTERVAL`", "`2`", "Seconds between hardware samples (at least 0.5)."],
            ["`MIRA_HARDWARE_RETENTION_HOURS`", "`24`", "How long hardware samples are kept."],
            ["`MIRA_DASHBOARD_UI`", "unset", "Set to `legacy` to serve the previous dashboard at `/`."],
          ],
        ),
        p(
          "The server listens on the address you give it and sends nothing out. The fonts and charts are part of the page, so it works without internet access.",
        ),
      ],
    },
  ],
};

export const detect: DocPage = {
  slug: "detect",
  title: "Detect",
  group: "dashboard",
  summary: "Run live detection from a camera or check one image, and record the run as a session.",
  lead: "Detect is the first page. It shows the live preview with boxes, tells you the next step when something is missing, and starts and stops sessions.",
  sections: [
    {
      id: "source",
      title: "Camera or image",
      blocks: [
        p(
          "The switch at the top right chooses the source. **Connected camera** runs live detection. **Image file** checks one JPEG or PNG with the model that is loaded, up to 8 MB and 16 megapixels. An image check needs the stream to be stopped, and its result is not added to any session.",
        ),
      ],
    },
    {
      id: "start",
      title: "Start a stream",
      blocks: [
        p(
          "One button above the preview always shows the next step: **Connect camera**, **Load model**, **Start stream**, and **Stop stream** while it runs. The camera and the model come from the settings you applied on the Settings page. If no model is chosen yet, the button opens Settings.",
        ),
        list(
          [
            "Open **Settings**, choose the camera and the model, and press **Apply settings**.",
            "Come back to **Detect** and press the button until it says **Stop stream**.",
          ],
          true,
        ),
        p(
          "The API refuses to start a stream until a camera and a model are ready. Settings are locked while the stream runs, so press **Stop stream** first.",
        ),
      ],
    },
    {
      id: "preview",
      title: "The preview",
      blocks: [
        p(
          "The preview draws a box and a label for every object. **Min. confidence** (0.05 to 1) hides boxes and list entries below the value you choose. It only changes what you see; the thresholds the model uses are on Settings. Under the preview, one line shows the frames per second, the time per frame and the number of objects in view.",
        ),
        p("The **Detections** list on the right shows the objects in the current frame, highest confidence first."),
      ],
    },
    {
      id: "session",
      title: "Record a session",
      blocks: [
        p(
          "The **Session** card on the right records the run. Type a name if you like, or leave it empty to get `Session YYYY-MM-DD HH:MM`, then press **Start session**. While the stream runs, every detection and a metrics sample (frames per second, latency, processor and memory) are saved to the session. **Stop session** ends it. Only one camera session can be active at a time.",
        ),
        p("The recorded run appears on the [Sessions](/docs/sessions) page."),
      ],
    },
    {
      id: "behaviour",
      title: "Behaviour to know",
      blocks: [
        list([
          "Detections below the larger of the confidence and the reject threshold are discarded before they are counted or recorded.",
          "The defaults are 0.25 confidence, 0.25 reject, 0.45 IoU, tracking on and 1000 ms target latency.",
          "For INT8 TFLite models the confidence threshold is capped at 0.25, and tracking is off for every TFLite model.",
          "Tracking uses the `lap` package, which is installed with `mira-ai` from version 1.1.0.",
        ]),
      ],
    },
  ],
};

export const sessions: DocPage = {
  slug: "sessions",
  title: "Sessions and replay",
  group: "dashboard",
  summary: "Every recorded run, its totals, a replayable timeline, notes and deletion.",
  lead: "A session is one run: a stretch of live detection, a checked video, or a batch of images. It keeps its detections and metrics, so you can look at it again later.",
  sections: [
    {
      id: "what",
      title: "What a session holds",
      blocks: [
        table(
          "Fields of a session",
          ["Field", "Meaning"],
          [
            ["`source`", "`camera`, `image`, `video` or `batch`."],
            ["`status`", "`active` while it records, then `completed`, or `failed`."],
            ["`model_name`", "The model that produced the detections."],
            ["Detections", "Time, frame index, class, confidence, box and track id."],
            ["Metrics", "Frames per second, latency, processor and memory, sampled while it ran."],
          ],
        ),
        p(
          "Camera sessions are started from [Detect](/docs/detect). Video and image sessions are created by an [import](/docs/batch-import).",
        ),
      ],
    },
    {
      id: "list",
      title: "The list",
      blocks: [
        p(
          "The Sessions page lists runs newest first. A camera session that is still recording shows a **Live** badge. **Load more** adds older runs. A session that is still active cannot be deleted, and the page says why.",
        ),
      ],
    },
    {
      id: "detail",
      title: "One session",
      blocks: [
        p(
          "A session page shows the totals, the class breakdown, the [export](/docs/export) links, and fields for the name and your notes. **Delete** asks for confirmation and removes the session with its detections and metrics.",
        ),
      ],
    },
    {
      id: "replay",
      title: "Replay",
      blocks: [
        p(
          "The replay plays a finished session back on a timeline. The timeline is cut into time buckets, at most 240 columns wide. A scrubber moves to any point. **Play** and **Pause** start and stop it, and the speed is 1x (the recorded pace), 2x or 4x. Stacked bars show the class mix over time, and the list underneath shows the detections in the current bucket. Playback pauses when the browser tab is hidden.",
        ),
        note(
          "Long sessions",
          "The replay reads detections in pages of 500, up to 5000 rows. A notice says when a session is longer than that and the replay is cut short. The totals and the exports always use every detection.",
        ),
      ],
    },
  ],
};

export const exportPage: DocPage = {
  slug: "export",
  title: "Export and reports",
  group: "dashboard",
  summary: "Download a session as CSV or JSON, or open a one-page report that prints to PDF.",
  lead: "Each session can leave the dashboard in three forms: a CSV file for spreadsheets, a JSON file with everything, and a one-page report for a write-up or a poster.",
  sections: [
    {
      id: "csv",
      title: "CSV",
      blocks: [
        p("One row per detection, with this header. The file is streamed, so large sessions download without waiting."),
        code("ts,offset_seconds,frame_index,class_name,confidence,x1,y1,x2,y2,track_id", "CSV header"),
        p("`offset_seconds` counts from the start of the session. The box is `x1,y1,x2,y2` in pixels of the frame."),
      ],
    },
    {
      id: "json",
      title: "JSON",
      blocks: [
        p(
          "The JSON file has four parts: `session`, `class_counts`, `detections` (the same fields as the CSV) and `metrics` (the samples taken while the session ran).",
        ),
      ],
    },
    {
      id: "report",
      title: "One-page report",
      blocks: [
        p(
          "The report is an HTML page with its own styles and charts. It makes no network requests, so it opens offline, and it is laid out to fit one A4 page when printed. Choose **Print** in the browser and **Save as PDF** to get a PDF.",
        ),
        list([
          "Title, session name, date, model and duration.",
          "Total detections and average confidence.",
          "A class table and a bar chart per class.",
          "Detections over time.",
          "Your notes.",
        ]),
        p(
          "The footer always says: Session counts describe this run only and are not real-world sorting accuracy. Text you typed is escaped, so a session name cannot change the page.",
        ),
      ],
    },
    {
      id: "api",
      title: "From a script",
      blocks: [
        code(
          lines(
            "curl -O -J http://127.0.0.1:8000/api/v1/sessions/<id>/export.csv",
            "curl -O -J http://127.0.0.1:8000/api/v1/sessions/<id>/export.json",
            "curl http://127.0.0.1:8000/api/v1/sessions/<id>/report.html",
          ),
        ),
        p(
          "Add `?download=1` to the report address to get it as a file. The session ids come from `GET /api/v1/sessions`; see the [API reference](/docs/api-v1).",
        ),
      ],
    },
  ],
};

export const compareBenchmark: DocPage = {
  slug: "compare-benchmark",
  title: "Compare and benchmark",
  group: "dashboard",
  summary: "Run two to four models on the same image, or benchmark models on a dataset.",
  lead: "The Models page has two tabs. Compare puts models side by side on one image. Benchmark scores models on a whole dataset and uses the same engine as `mira benchmark`.",
  sections: [
    {
      id: "compare",
      title: "Compare",
      blocks: [
        p(
          "Pick two to four models and one JPEG or PNG (up to 8 MB), and set the confidence (0.05 to 1, default 0.25). The server runs the models one after the other on that image. For every model you see the annotated image, the time in milliseconds, the number of objects, the class counts and the average confidence.",
        ),
        p(
          "A short sentence points out the faster model and the one with more detections. It is a hint, not a verdict: one image says little about which model is better.",
        ),
        note(
          "Saved comparisons",
          "Past comparisons are kept with their numbers only. The images are not stored, and the page says so when you reopen one.",
        ),
      ],
    },
    {
      id: "benchmark",
      title: "Benchmark",
      blocks: [
        p(
          "Pick one to six models, optionally a dataset (a YOLO `dataset.yaml` or a folder, the project default if empty), a confidence and a maximum number of images. The run is a background job: it shows its progress, and you can cancel it.",
        ),
        p(
          "The results table lists mAP50, mAP50-95, precision, recall, F1 and the average time per image for each model, with a per-class view. Values the benchmark does not measure, such as frames per second, show as a dash and never as a number. Errors reported for one model are shown above the table.",
        ),
        warning(
          "What the numbers mean",
          "A benchmark score is measured on the dataset you chose, not on a real camera over a real bin. Compare scores from the same dataset only.",
        ),
      ],
    },
  ],
};

export const batchImport: DocPage = {
  slug: "batch-import",
  title: "Video and batch import",
  group: "dashboard",
  summary: "Run a model over a video, a set of images or a folder, with progress and cancel.",
  lead: "Import turns existing material into sessions. A video or a pile of images runs in the background while you keep working, and the result is a normal session.",
  sections: [
    {
      id: "video",
      title: "A video",
      blocks: [
        p(
          "On the Sessions page, choose **Video**. MP4, AVI, MOV and MKV files up to 500 MB are accepted. The model runs on every Nth frame; **Frame stride** sets N (default 5, from 1 to 120). A larger stride is faster and can miss objects that are only on screen briefly. The detections are stored with the time of their frame, so the replay matches the video.",
        ),
      ],
    },
    {
      id: "images",
      title: "Images or a folder",
      blocks: [
        p(
          "Choose image files (JPEG or PNG, up to 200 at a time), or give the path of a folder on the machine that runs the dashboard. A folder import takes at most 2000 JPEG or PNG files, does not go into sub-folders by default and does not follow symbolic links. It creates a session with the source `batch`.",
        ),
      ],
    },
    {
      id: "jobs",
      title: "Progress and cancel",
      blocks: [
        p(
          "Every import is a job. The panel shows its progress once a second, and **Cancel** stops it. When it finishes, the list reloads and the panel links to the new session. If you reload the page while a job runs, the page picks it up again.",
        ),
        table(
          "Job states",
          ["State", "Meaning"],
          [
            ["`queued`", "Waiting for a free worker."],
            ["`running`", "Working. The progress runs from 0 to 1."],
            ["`completed`", "Done. The session is ready."],
            ["`failed`", "Stopped by an error. The message says why."],
            ["`cancelled`", "You stopped it."],
          ],
        ),
      ],
    },
  ],
};

export const analytics: DocPage = {
  slug: "analytics",
  title: "Analytics and hardware",
  group: "dashboard",
  summary: "Charts for a session and the processor, memory and temperature history of the machine.",
  lead: "Analytics has three parts: the charts of one session, the health of the machine that runs the detector, and the sorting arm log.",
  sections: [
    {
      id: "session",
      title: "Session charts",
      blocks: [
        p(
          "Choose a session. **Objects over time** is a line chart of how many objects were in view, and the **class mix** lists how many of each class were found. Every chart has a **Show data table** button that lists its numbers as text.",
        ),
      ],
    },
    {
      id: "hardware",
      title: "Hardware",
      blocks: [
        p(
          "Four tiles show the current processor use, memory use, temperature and one-minute load. They refresh every 5 seconds. Below them a chart shows the history for 15 minutes, 1 hour, 6 hours or 24 hours. The history is sampled in the background while the dashboard runs and kept for 24 hours.",
        ),
        p(
          "The temperature comes from the first source the machine offers: the operating system's sensors, `/sys/class/thermal/thermal_zone0/temp`, or `vcgencmd measure_temp` on a Raspberry Pi. When none exists, as on many Windows machines, the tile says **No temperature sensor** and the chart is replaced by that message.",
        ),
      ],
    },
    {
      id: "arm",
      title: "Sorting arm",
      blocks: [
        p("The last panel belongs to the [sorting arm](/docs/sorting-arm): its state, an accuracy figure and the event log."),
      ],
    },
  ],
};

export const sortingArm: DocPage = {
  slug: "sorting-arm",
  title: "Sorting arm",
  group: "dashboard",
  summary: "The placeholder interface for the future sorting robot, its event log and its feedback.",
  lead: "The sorting robot does not exist yet. This part of the dashboard is the place where it will plug in, so the software around it can be built and tested first.",
  sections: [
    {
      id: "simulated",
      title: "Simulated only",
      blocks: [
        warning(
          "No robot connected",
          "Nothing in this part of the dashboard talks to hardware. The status always reports `connected: false` and `mode: simulated`, and the page shows the banner **No robot connected. Commands are simulated.**",
        ),
        p(
          "A command is `sort` (with a class), `home` or `stop`. The simulator writes a `sort_requested` event and, a moment later, a `sort_completed` event. Unknown classes are refused.",
        ),
      ],
    },
    {
      id: "log",
      title: "Event log and feedback",
      blocks: [
        p(
          "On Analytics, choose a class and press **Send simulated sort** to try it. The log lists every event. On a `sort_completed` event you can mark the result **correct** or **incorrect**. The accuracy figure is the share of correct answers among the answers given, and it reads **No feedback yet** until there is one.",
        ),
        p(
          "The same figure fills `sorting_accuracy` in `GET /api/statistics`. Because the arm is simulated, it measures your clicks, not a robot, and it is not real-world sorting accuracy.",
        ),
      ],
    },
    {
      id: "driver",
      title: "For a real arm later",
      blocks: [
        p(
          "The simulator sits behind an `ArmDriver` interface with one method, `send(command)`. A driver for real hardware can replace `SimulatedArm` without changing the API or the pages.",
        ),
      ],
    },
  ],
};

export const apiV1: DocPage = {
  slug: "api-v1",
  title: "Dashboard API v1",
  group: "reference",
  summary: "The /api/v1 endpoints for sessions, exports, compare, benchmark, batch, jobs, hardware and the arm.",
  lead: "Version 1 of the API sits under `/api/v1` next to the older routes described on the [Dashboard API](/docs/dashboard-api) page. It is JSON with snake_case names. Times in payloads are ISO 8601 in UTC. There is no authentication.",
  sections: [
    {
      id: "conventions",
      title: "Conventions",
      blocks: [
        table(
          "Error codes",
          ["Code", "Meaning"],
          [
            ["`404`", "Unknown id."],
            ["`409`", "Wrong state, for example deleting an active session."],
            ["`413`", "File too large."],
            ["`415`", "Wrong file type."],
            ["`422`", "Invalid input."],
          ],
        ),
        p(
          "Errors are `{\"detail\": \"...\"}` with a sentence you can show to a person. The class names are always `glass`, `metal`, `paper`, `plastic` and `trash`.",
        ),
      ],
    },
    {
      id: "sessions",
      title: "Sessions and exports",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/sessions", text: "Start a session: name, source, model_name. Only one camera session can be active." },
            { method: "POST", path: "/api/v1/sessions/{id}/stop", text: "End a session." },
            { method: "GET", path: "/api/v1/sessions", text: "List sessions: limit, offset, status." },
            { method: "GET", path: "/api/v1/sessions/{id}", text: "One session with its config and notes." },
            { method: "PATCH", path: "/api/v1/sessions/{id}", text: "Change the name or the notes." },
            { method: "DELETE", path: "/api/v1/sessions/{id}", text: "Delete a session with its detections and metrics (409 if active)." },
            { method: "GET", path: "/api/v1/sessions/{id}/detections", text: "Detections: limit, offset, class_name, min_confidence." },
            { method: "GET", path: "/api/v1/sessions/{id}/timeline", text: "Buckets for the replay: bucket_seconds." },
            { method: "GET", path: "/api/v1/sessions/{id}/export.csv", text: "CSV download." },
            { method: "GET", path: "/api/v1/sessions/{id}/export.json", text: "JSON download." },
            { method: "GET", path: "/api/v1/sessions/{id}/report.html", text: "One-page report; add ?download=1 for a file." },
          ],
        },
      ],
    },
    {
      id: "models",
      title: "Compare and benchmark",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/compare", text: "Multipart: image, models (2 to 4 names, comma separated), confidence." },
            { method: "GET", path: "/api/v1/compare", text: "Past comparisons without images." },
            { method: "GET", path: "/api/v1/compare/{id}", text: "One comparison." },
            { method: "DELETE", path: "/api/v1/compare/{id}", text: "Delete a comparison." },
            { method: "POST", path: "/api/v1/benchmark/runs", text: "Start a benchmark: models, dataset, confidence, max_images. Returns run_id and job_id." },
            { method: "GET", path: "/api/v1/benchmark/runs", text: "Past runs." },
            { method: "GET", path: "/api/v1/benchmark/runs/{id}", text: "One run with its results." },
            { method: "DELETE", path: "/api/v1/benchmark/runs/{id}", text: "Delete a run." },
          ],
        },
      ],
    },
    {
      id: "jobs",
      title: "Batch and jobs",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/batch/video", text: "Multipart: video, model_name, confidence, frame_stride, name. Returns job_id and session_id." },
            { method: "POST", path: "/api/v1/batch/images", text: "Multipart images, or JSON with a directory. Returns job_id and session_id." },
            { method: "GET", path: "/api/v1/jobs", text: "Recent jobs." },
            { method: "GET", path: "/api/v1/jobs/{id}", text: "One job: status, progress, message, result, error." },
            { method: "POST", path: "/api/v1/jobs/{id}/cancel", text: "Cancel a job (409 once it has finished)." },
          ],
        },
        p("Starting a job answers `202`. Poll the job, or listen to the events socket below."),
      ],
    },
    {
      id: "hardware",
      title: "Hardware and arm",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "GET", path: "/api/v1/hardware/current", text: "Processor, memory, temperature, load, platform and core count." },
            { method: "GET", path: "/api/v1/hardware/history", text: "Averaged points: minutes, points." },
            { method: "GET", path: "/api/v1/arm/status", text: "Always simulated: connected, mode, state, accuracy." },
            { method: "POST", path: "/api/v1/arm/commands", text: "Send a simulated command: sort, home or stop." },
            { method: "GET", path: "/api/v1/arm/events", text: "The event log: limit, kind." },
            { method: "POST", path: "/api/v1/arm/events/{id}/feedback", text: "Mark a completed sort as correct or incorrect." },
            { method: "GET", path: "/api/v1/arm/accuracy", text: "Correct, total and the accuracy." },
          ],
        },
      ],
    },
    {
      id: "events",
      title: "Events socket",
      blocks: [
        {
          type: "endpoints",
          items: [{ method: "WS", path: "/ws/v1/events", text: "Live events for jobs, sessions, the arm and the hardware." }],
        },
        p(
          "On connect the server sends `{\"type\": \"hello\", \"ts\": ..., \"data\": {\"version\": 1}}`, then every event as `{\"type\", \"ts\", \"data\"}`. The types are `session_started`, `session_stopped`, `job_progress`, `job_finished`, `arm_event`, `hardware_sample` and `detection_batch`. A `ping` arrives every 20 seconds. A slow client loses events and never slows the server down.",
        ),
      ],
    },
  ],
};

export const troubleshooting: DocPage = {
  slug: "troubleshooting",
  title: "Troubleshooting",
  group: "help",
  summary: "Common problems with the dashboard and what to do about them.",
  lead: "If something does not work, find the symptom below. If it is not listed, open an issue on GitHub and say what you saw.",
  sections: [
    {
      id: "dashboard",
      title: "The dashboard",
      blocks: [
        table(
          "Problems and fixes",
          ["What you see", "Why, and what to do"],
          [
            [
              "The old dashboard opens instead of the new one",
              "The new interface is not built. A PyPI install contains it. In a source checkout run `corepack pnpm install` and `corepack pnpm build` in `src/dashboard/ui`, then restart.",
            ],
            ["The page does not open", "Check the address and the port. Start it on another port with `mira dashboard --port 8080` if 8000 is taken."],
            [
              "Start stream does nothing, or the button asks for a step",
              "A camera and a model are needed first. Follow the button on [Detect](/docs/detect): connect the camera, then load the model.",
            ],
            ["Settings cannot be changed", "They are locked while the stream runs. Press **Stop stream** first."],
            ["An image is refused", "Only JPEG and PNG up to 8 MB and 16 megapixels are accepted, and the stream has to be stopped."],
            ["A session cannot be deleted", "It is still active. Stop it first."],
            ["The replay stops early", "A notice says so: the replay reads up to 5000 detections. The exports contain all of them."],
            ["No temperature in Analytics", "The machine reports no sensor. This is normal on many Windows computers."],
          ],
        ),
      ],
    },
    {
      id: "imports",
      title: "Imports",
      blocks: [
        list([
          "A video is refused: use MP4, AVI, MOV or MKV and keep it under 500 MB.",
          "A folder import finds nothing: the folder has to exist on the machine that runs the dashboard, and only JPEG and PNG files directly inside it are used.",
          "An import seems stuck: a long video with a stride of 1 takes a long time. Raise the stride or press **Cancel**.",
        ]),
      ],
    },
  ],
};

export const faq: DocPage = {
  slug: "faq",
  title: "FAQ",
  group: "help",
  summary: "Short answers about privacy, accuracy, hardware and where things are kept.",
  lead: "Short answers to questions that come up often.",
  sections: [
    {
      id: "privacy",
      title: "Does it send my data anywhere?",
      blocks: [
        p(
          "No. The dashboard runs on your computer and listens on `127.0.0.1` unless you change it. Detections are stored in a local SQLite file, and no frames are saved. The pages load no fonts or scripts from other sites.",
        ),
      ],
    },
    {
      id: "accuracy",
      title: "How accurate is it?",
      blocks: [
        p(
          "The headline score, 90.58% mAP50, was measured on 415 validation photos, not on a real camera. See the [research report](/research) and the [limitations](/docs/limitations). The dashboard's own counts describe one run and are not real-world sorting accuracy.",
        ),
      ],
    },
    {
      id: "robot",
      title: "Can it control a robot?",
      blocks: [
        p(
          "Not yet. The robot is not built. The [sorting arm](/docs/sorting-arm) interface is a simulation that exists so the software can be prepared.",
        ),
      ],
    },
    {
      id: "location",
      title: "Where is my data, and how do I reset it?",
      blocks: [
        p(
          "In `~/.mira/dashboard.db`, or the file named by `MIRA_DASHBOARD_DB`. Stop the dashboard and delete that file to start with an empty history.",
        ),
      ],
    },
    {
      id: "update",
      title: "How do I update?",
      blocks: [
        code("python -m pip install --upgrade mira-ai"),
        p("The history is kept. New versions add tables to the same file and leave your sessions alone."),
      ],
    },
  ],
};

