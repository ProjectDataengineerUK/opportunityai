import Link from "next/link";
import { getOpportunity } from "@/lib/api";
import { OpportunityDetail } from "./OpportunityDetail";

interface PageProps {
  params: { id: string };
}

export default async function OpportunityPage({ params }: PageProps) {
  let opportunity;
  try {
    opportunity = await getOpportunity(params.id);
  } catch {
    return (
      <main className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-red-500">Vaga não encontrada.</p>
        <Link href="/" className="text-blue-600 hover:underline mt-4 block">
          ← Voltar ao dashboard
        </Link>
      </main>
    );
  }

  return <OpportunityDetail initial={opportunity} />;
}
