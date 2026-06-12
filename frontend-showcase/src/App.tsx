import { AgentTeam } from "./components/AgentTeam";
import { Architecture } from "./components/Architecture";
import { DemoFlow } from "./components/DemoFlow";
import { FinalCta } from "./components/FinalCta";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import { Navbar } from "./components/Navbar";
import { ProblemSolution } from "./components/ProblemSolution";
import { ShowcaseNote } from "./components/ShowcaseNote";
import { SponsorTools } from "./components/SponsorTools";
import { Team } from "./components/Team";

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <ProblemSolution />
        <AgentTeam />
        <DemoFlow />
        <Architecture />
        <SponsorTools />
        <ShowcaseNote />
        <Team />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}

