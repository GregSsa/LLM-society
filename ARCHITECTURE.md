# Architecture — Simulation socio-technique

Résumé
- Système modulaire en Python.
- Agents: objets stateful (personnalité, opinion, émotion, paramètres).
- LLM: interface abstraite, possibilité de simuler (dummy) ou d'appeler API.
- Simulateur: orchestrateur de tours, logique de pair/interaction, journalisation.
- Règles de mise à jour: fonctions séparées pour opinion/emotion (decay, contagion).
- Visualisation & métriques: pipeline séparé.

Composants

1) Agent (src/agent.py)
- Attributs: id, personality_prompt, state (opinion, valence, arousal), openness, trust, sociability.
- Méthodes: choose_partner, generate_message, receive_message, step.

2) LLM Interface (src/llm_interface.py)
- Classe abstraite LLMInterface.
- Implémentations: DummyLLM, wrapper OpenAIClient (à implémenter séparément).

3) Simulateur (src/simulator.py)
- Boucle de simulation par pas.
- Journalisation JSONL/CSV (events), snapshots pour métriques.

4) Update rules (src/update_rules.py)
- Fonctions d'update pour opinion & émotion (decay, contagion, influence).

5) Metrics (src/metrics.py)
- Polarisation, moyenne/opinion, clustering, vitesse de propagation.

6) Visualisation (src/viz.py)
- Timeseries, heatmaps, scatter (opinion vs valence), graph social.

Extensibilité & recommandations
- Séparer I/O LLM et logique CPU pour tests.
- Fournir DummyLLM pour expérimentations sans coûts.
- Supporter random seeds et runs batch.
- Option réseau social (ER, small-world, scale-free).