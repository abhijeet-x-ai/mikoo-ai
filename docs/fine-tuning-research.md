# Self-contained Mikoo training research note

Mikoo's training corpus must be assembled from data that the project can legally use, transform, and redistribute. The source manifest should record the original repository or author, path, commit, license, attribution text, checksum, opt-out state, and whether redistribution is permitted. A missing or unclear license is a rejection reason.

Recommended sources are authored examples, contributor-approved code, permissively licensed repositories, generated examples produced under terms that permit training, and real issue/patch/test records whose redistribution rights are documented. Source code, documentation, tests, compiler messages, configuration files, and repair trajectories should be normalized into Mikoo's common record schema.

Do not use private code, credentials, personal data, copied benchmark answers, hidden evaluation patches, malware payloads, or code with unclear redistribution rights. Keep evaluation repositories and prompts isolated from training. Every training record must be deduplicated, provenance-preserving, and linked to an actual test or compiler result when it claims a repair.

The model should learn from the engineering loop: request, bounded context, plan, minimal patch, test or compiler feedback, correction, and truthful final report. The first release should prioritize verified repair trajectories, test generation, repository context selection, and safe tool actions over the volume of raw code.

Inference is fully local and requires no network service. Teacher-generated records, if used during training, must be exported into the local dataset with teacher terms, prompt, output, filter decision, and verification status recorded. The teacher is not part of the Mikoo Android runtime.
