<script lang="ts">
  import { getDictionary } from '$i18n';
  import { getPackageCopy } from '$i18n/package';
  import Seo from '$lib/components/Seo.svelte';
  import Commands from '$lib/components/package/Commands.svelte';
  import Install from '$lib/components/package/Install.svelte';
  import Judged from '$lib/components/package/Judged.svelte';
  import Links from '$lib/components/package/Links.svelte';
  import Models from '$lib/components/package/Models.svelte';
  import PackageHeader from '$lib/components/package/PackageHeader.svelte';
  import Quickstart from '$lib/components/package/Quickstart.svelte';
  import Requirements from '$lib/components/package/Requirements.svelte';
  import ResearchShell from '$lib/components/research/ResearchShell.svelte';
  import Status from '$lib/components/package/Status.svelte';

  /**
   * The developer's route: a README with good typography. What the package is, a four step quickstart, install,
   * how a detection is judged, the command reference, the models, requirements, an honest status and the
   * download figure. Words are in src/i18n/package; commands, flags, files and scores are in
   * lib/components/package/package-data.ts.
   */
  let { data } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));
  const t = $derived(getPackageCopy(lang));
  const meta = $derived(dict.meta.pages.package);

  const SECTION_IDS = ['quickstart', 'install', 'judged', 'commands', 'models', 'requirements', 'status', 'links'] as const;
  const sections = $derived(SECTION_IDS.map((id) => ({ id, label: t.contents[id] })));
</script>

<Seo {lang} path="/package" title={meta.title} description={meta.description} />

<PackageHeader {lang} {dict} {t} />

<ResearchShell {lang} {sections} label={meta.title}>
  <Quickstart {lang} {dict} {t} />
  <Install {dict} {t} />
  <Judged {lang} {dict} {t} />
  <Commands {lang} {t} />
  <Models {lang} {dict} {t} />
  <Requirements {lang} {t} />
  <Status {lang} {t} />
  <Links {lang} {dict} {t} />
</ResearchShell>
