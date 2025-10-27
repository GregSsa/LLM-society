# Simulation socio-technique : Agents LLM et propagation d’émotions / opinions

But
- Simuler une population d'agents LLM, chacun défini par un prompt (personnalité, opinion, émotion).
- Étudier dynamiques collectives : contagion émotionnelle, polarisation, formation de clusters.
- Fournir métriques et visualisations (courbes d'opinion, carte de clusters, heatmap d'émotions).

Points clés
- Agents encapsulant un LLM interne (interface abstraite pour OpenAI / API locale / dummy).
- Boucle de simulation par tours : sélection d'interlocuteurs, échanges textuels, mises à jour d'état.
- Règles d'influence simples (pondération, confiance, ouverture).
- Modules pour métriques et visualisation.

Quickstart
1. Créez l'environnement conda (ou installez requirements.txt) :
   conda env create -f environment.yml
   conda activate llm-society
2. Lancer une simulation d'exemple:
   python -m src.simulator --config configs/population.yaml --steps 200
3. Visualisations et logs seront dans `outputs/`.

Structure recommandée
- README.md
- ARCHITECTURE.md
- src/
  - agent.py
  - llm_interface.py
  - simulator.py
  - update_rules.py
  - metrics.py
  - viz.py
  - utils.py
- configs/
  - population.yaml
- outputs/
- environment.yml
- requirements.txt

Licence
- MIT (exemple)