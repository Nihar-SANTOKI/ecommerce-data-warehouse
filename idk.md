flowchart TD
  subgraph Inputs
    A1[Job Description]
    A2[Personal Information]
    A3[Skills (opt.)]
    A4[Projects/Experience (opt.)]
    A5[CV Model]
  end

  subgraph Preprocessing
    P1[Validate & Normalize]
    P2[Enrich & Tokenize]
  end

  subgraph AI Engine
    G1[Prompt Builder]
    G2[Generative AI Model]
    G3[Post‑Gen Analyzer]
  end

  subgraph Postprocessing
    Q1[Section Editor UI]
    Q2[Formatting & Templating]
    Q3[Export Engine]
  end

  subgraph Outputs
    O1[Downloadable PDF]
    O2[Downloadable Word (.docx)]
  end

  %% Flows
  A1 --> P1
  A2 --> P1
  A3 --> P1
  A4 --> P1
  A5 --> P1

  P1 --> P2
  P2 --> G1
  G1 --> G2
  G2 --> G3

  G3 --> Q1
  Q1 --> Q2
  Q2 --> Q3
  Q3 --> O1 & O2
