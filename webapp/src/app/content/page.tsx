import { load } from "@/lib/store";
import { ContentStudio } from "@/components/ContentStudio";
import { ProposalCard } from "@/components/Actions";

export const dynamic = "force-dynamic";

export default function Content() {
  const s = load();
  const props = s.proposals.filter((p) => p.status === "pending" && p.agent === "Content studio agent");
  return (
    <div>
      <h2>Content studio agent</h2>
      <p className="lead">Makes marketing pictures and short videos for Instagram, Facebook, YouTube, LinkedIn, TikTok, X and WhatsApp status, with captions in several languages. Each picture and video is laid out for the platform's size and safe zones (story bars, reel buttons). It only uses your verified claims and never posts: you approve, then you publish.</p>
      <ContentStudio products={s.products} verified={s.settings.verifiedClaims} />
      {props.map((p) => <ProposalCard key={p.id} p={p} />)}
    </div>
  );
}
