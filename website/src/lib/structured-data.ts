import type { Locale } from "../i18n/config";
import { getDictionary } from "../i18n";
import {
  DATASET_ORIGINS_URL,
  EXPERIMENT_LOG_URL,
  FACTS,
  GITHUB_URL,
  HF_URL,
  LICENSE_URL,
  PYPI_URL,
  SITE_DESCRIPTION,
  SITE_NAME,
  SITE_URL,
} from "./site";

type StructuredDataInput = {
  lang: Locale;
  inLanguage?: Locale | readonly Locale[];
  path: string | null;
  canonicalUrl: string;
  title: string;
  description: string;
};

/** Build safe, crawlable JSON-LD for the page and the MIRA software it describes. */
export function structuredDataScript({
  lang,
  inLanguage = lang,
  path,
  canonicalUrl,
  title,
  description,
}: StructuredDataInput): string {
  const websiteId = `${SITE_URL}/#website`;
  const softwareId = `${SITE_URL}/#software`;
  const sourceId = `${SITE_URL}/#source-code`;
  const modelsId = `${SITE_URL}/#model-repository`;
  const researchFactId = `${SITE_URL}/#exp019-validation-result`;
  const hasResearchFact = path === "/" || path === "/research";
  const researchObservation = {
    "@type": "Observation",
    "@id": researchFactId,
    name: "MIRA EXP-019 validation result",
    observationAbout: { "@id": softwareId },
    measuredProperty: { "@type": "PropertyValue", name: "mAP50" },
    measuredValue: { "@type": "QuantitativeValue", value: FACTS.exp019Map50, unitText: "%" },
    measurementTechnique: `Validation on the ${FACTS.validationImages}-image TrashNet tabletop split`,
    description: "Validation result only; it does not establish real-world sorting accuracy.",
    citation: EXPERIMENT_LOG_URL,
    isPartOf: { "@id": `${canonicalUrl}#webpage` },
  };

  const graph = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": websiteId,
        url: `${SITE_URL}/`,
        name: SITE_NAME,
        description: SITE_DESCRIPTION,
        inLanguage: ["en", "de"],
      },
      {
        "@type": "WebPage",
        "@id": `${canonicalUrl}#webpage`,
        url: canonicalUrl,
        name: title,
        description,
        inLanguage,
        isPartOf: { "@id": websiteId },
        about: { "@id": softwareId },
        mainEntity: { "@id": hasResearchFact ? researchFactId : softwareId },
      },
      {
        "@type": "SoftwareApplication",
        "@id": softwareId,
        name: SITE_NAME,
        alternateName: "Machine Intelligence for Recycling Automation",
        description: getDictionary(lang).meta.description,
        url: SITE_URL,
        applicationCategory: "DeveloperApplication",
        operatingSystem: "Cross-platform",
        downloadUrl: PYPI_URL,
        subjectOf: [{ "@id": sourceId }, { "@id": modelsId }],
        citation: [EXPERIMENT_LOG_URL, DATASET_ORIGINS_URL],
      },
      {
        "@type": "SoftwareSourceCode",
        "@id": sourceId,
        name: "MIRA source code",
        url: GITHUB_URL,
        codeRepository: GITHUB_URL,
        programmingLanguage: "Python",
        license: LICENSE_URL,
        isPartOf: { "@id": softwareId },
      },
      {
        "@type": "CreativeWork",
        "@id": modelsId,
        name: "MIRA model repository",
        url: HF_URL,
        about: { "@id": softwareId },
      },
      ...(hasResearchFact ? [researchObservation] : []),
    ],
  };

  // Prevent a description containing </script> from terminating the JSON-LD element.
  return JSON.stringify(graph).replace(/</g, "\\u003c");
}
