## Question

We do not have the LIC PDFs downloaded yet. We need to decide on the data sourcing strategy:
1. Do we scrape/download directly from the official LIC India website (pros: official, cons: PDFs might be image-based or badly formatted)?
2. Or do we scrape from third-party aggregators like PolicyBazaar/Ditto (pros: data might already be in cleaner HTML/tables, cons: might be slightly outdated or unauthorized)?
3. If we stick to PDFs, how do we automate the initial gathering of the top 10-15 active policies?

*Label: wayfinder:research (AFK / HITL)*

---

## Resolution

- **Source**: Official LIC India website (licindia.in) to guarantee 100% accuracy and compliance.
- **Gathering Method**: Manual gathering for v1.0. We only need 10-15 major active policies to validate the RAG architecture. Building a resilient scraper is overkill for this phase.
- **Storage**: PDFs will be manually downloaded and placed in the `data/raw_pdfs/` directory locally before being pushed to a GCS bucket later.

*Status: Closed*
