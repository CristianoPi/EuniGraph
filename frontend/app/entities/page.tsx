import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { PublicationsPreview } from "@/components/widgets/publications-preview";

export default function EntitiesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Entities"
        title="A stable base for browsing the canonical catalog."
        description="This route is the future home for publication, researcher and organization browsing. For now it proves the frontend can query backend entities and render useful placeholder states."
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Panel
          title="Publication preview"
          description="First live read against the canonical publication API."
        >
          <PublicationsPreview />
        </Panel>

        <Panel
          title="Planned entity slices"
          description="The next frontend issues can fill these areas without changing the route map."
        >
          <div className="grid gap-3">
            {[
              "Publication list and detail surfaces",
              "Researcher browsing and affiliation context",
              "Organization pages with graph and semantic entry points",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.25rem] border border-[color:var(--border)] bg-white/70 px-4 py-4 text-sm leading-6 text-slate-700"
              >
                {item}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
