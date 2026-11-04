# External evidence and model-training policy

TherapyBot separates four artifacts: **(1) source pointers**, **(2) source-linked original summaries**, **(3) original synthetic training/evaluation examples**, and **(4) third-party full text**. The first three can be committed when records contain accurate metadata and no personal information; the fourth is not included by default.

For each source record: keep stable ID, authors/issuer, title, URL/DOI, publication/update and retrieval dates, study design/evidence class, claim summary, limitations (population, bias, certainty), and rights status. Mark unclear rights as unknown, not permissive. Source relevance does not imply clinical effectiveness of TherapyBot.

Research priorities: clinical methods (CBT, DBT, ACT, behavioral activation, trauma-informed responses); psychiatry and neuroscience uncertainty; sociological determinants, relationships and isolation; scientific falsifiers; safety and risk assessment standards.

The synthetic examples should test **both** missed urgent risk and false alarm, as well as diagnostic overreach, unsupported spiritual claims, medication advice, social stereotypes, treatment claims, memory consent and prompt injection. Do not train on a patient's text or on extensive third-party copyrighted passages. Generated examples must be labeled original and linked to sources; a reviewer must still approve any training-data release and model choice. It is valid to use examples solely as evaluation fixtures until training rights and model behavior are qualified.

Initial authoritative references include NIMH Psychotherapies and Psychosis guidance, NICE NG222/NG225, WHO World Mental Health Report, CDC Social Connection, and 988. Peer-reviewed external research is indexed separately, not assumed to be a clinical guideline.
