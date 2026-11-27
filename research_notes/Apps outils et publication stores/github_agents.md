# Dépôts GitHub open source pour construire des agents IA et étendre Claude Code (état au 19/11/2026)

> Méthode : chaque dépôt a été ouvert sur sa page GitHub (via WebFetch) le 19/11/2026. Étoiles et licences = valeurs affichées ce jour-là, arrondies comme GitHub les arrondit. « Dernière activité » = date « Updated » affichée sur les listes d'organisation/topics GitHub ; quand la page du dépôt ne l'affichait pas, c'est noté « non vérifiée ». L'API GitHub et `gh` étaient bloqués dans cet environnement, donc les dates exactes du dernier commit n'ont pas pu être lues.
> Avertissement : en 2026, beaucoup de dépôts « tendance » affichent des centaines de milliers d'étoiles (par ex. `morluto/rea` 469k, `affaan-m/ECC` 307k sur le topic claude-code). Le nombre d'étoiles n'est plus un signal fiable de qualité ou de sécurité (achat d'étoiles possible, effet de mode).

## 1. Frameworks d'agents : lesquels conviennent à un créateur solo qui utilise surtout Claude ?

### Takeaway
Pour une équipe d'agents centrée sur Claude, la base la plus directe est **Claude Code + Claude Agent SDK (Python/TS) + serveurs MCP**, avec **n8n auto-hébergé** pour les automatisations planifiées (publication, notifications). LangGraph, CrewAI, Pydantic AI et smolagents sont de bonnes alternatives multi-modèles ; **AutoGen est archivé** et ne doit plus servir à un nouveau projet.

### Cited Findings
**Officiel Anthropic**
- `anthropics/claude-agent-sdk-python` : https://github.com/anthropics/claude-agent-sdk-python. Environ 8,6k étoiles, licence MIT, mis à jour le 19/11/2026. C'est le SDK Python qui expose la boucle d'agent de Claude Code. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-agent-sdk-typescript` : https://github.com/anthropics/claude-agent-sdk-typescript. Environ 1,9k étoiles, aucune licence affichée par GitHub (non vérifiée, probablement les conditions commerciales Anthropic plutôt qu'une licence OSI), mis à jour le 19/11/2026. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-agent-sdk-demos` : environ 2,8k étoiles, pas de licence affichée, mis à jour le 27/08/2026. Démos du SDK. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-cookbooks` (ancien nom : anthropic-cookbook) : https://github.com/anthropics/claude-cookbooks. Environ 55k étoiles, MIT, mis à jour le 17/11/2026. Notebooks et recettes (outils, RAG, agents). — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-quickstarts` : environ 21k étoiles, MIT, mis à jour le 06/11/2026. Projets de démarrage sur l'API Claude. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/commerce-agents` (3,5k, Apache-2.0, 16/11/2026) : modèle d'agents d'achat et de vente. `anthropics/sandbox-runtime` (7,2k, Apache-2.0, 13/11/2026) : sandbox au niveau du système pour limiter les fichiers et le réseau, sans conteneur. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- SDK API : `anthropic-sdk-python` (4,1k, Apache-2.0) et `anthropic-sdk-typescript` (2,2k, Apache-2.0), tous deux mis à jour le 17/11/2026. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)

**MCP (Model Context Protocol)**
- `modelcontextprotocol/servers` : https://github.com/modelcontextprotocol/servers. Environ 92k étoiles, licence « Other » selon GitHub, mis à jour le 18/11/2026. Ce sont les serveurs de référence. Les serveurs qui ne sont plus maintenus sont dans `servers-archived` (archivé). — [Org MCP](https://github.com/orgs/modelcontextprotocol/repositories?q=&type=all&sort=stargazers)
- SDK : `python-sdk` (25k, MIT, 17/11/2026) et `typescript-sdk` (14k, « Other », 19/11/2026). — [Org MCP](https://github.com/orgs/modelcontextprotocol/repositories?q=&type=all&sort=stargazers)
- `modelcontextprotocol/inspector` (11k, 18/11/2026) : outil de test des serveurs MCP. `registry` (7,5k, 18/11/2026) : registre communautaire des serveurs. `modelcontextprotocol` (9,7k) : spécification et documentation. `ext-apps` (3,1k) : interfaces intégrées servies par MCP. `ext-skills` (802, Apache-2.0) : distribution de Skills par MCP. `mcpb` (2,2k, 26/05/2026) : installation en un clic de serveurs locaux. — [Org MCP](https://github.com/orgs/modelcontextprotocol/repositories?q=&type=all&sort=stargazers)

**Frameworks tiers**
- `langchain-ai/langgraph` : https://github.com/langchain-ai/langgraph. Environ 45,1k étoiles, MIT, non archivé, date du dernier commit non vérifiée. « Low-level orchestration framework for building stateful agents. » — [GitHub](https://github.com/langchain-ai/langgraph)
- `langchain-ai/langchain` : environ 150k étoiles, mis à jour le 19/11/2026. — [Topic ai-agents](https://github.com/topics/ai-agents)
- `crewAIInc/crewAI` : https://github.com/crewAIInc/crewAI. Environ 61,1k étoiles, MIT, non archivé (478 issues et 785 PR ouvertes), date non vérifiée. Agents organisés par rôles, ce qui colle à l'idée d'« équipe ». — [GitHub](https://github.com/crewAIInc/crewAI)
- `microsoft/autogen` : https://github.com/microsoft/autogen. Environ 61,9k étoiles, MIT (documentation en CC-BY-4.0). Le dépôt est **archivé**. Microsoft n'y apporte plus de correctifs, même de sécurité, et recommande « Microsoft Agent Framework » pour les nouveaux projets. — [GitHub](https://github.com/microsoft/autogen)
- `ag2ai/ag2` (fork communautaire d'AutoGen) : https://github.com/ag2ai/ag2. Environ 5,1k étoiles, Apache-2.0, date non vérifiée. « AG2 (formerly AutoGen): The Open-Source AgentOS ». — [GitHub](https://github.com/ag2ai/ag2)
- `openai/openai-agents-python` : https://github.com/openai/openai-agents-python. Environ 30,8k étoiles, MIT. Il se dit agnostique du fournisseur (plus de 100 LLM via LiteLLM ou any-llm en option), mais Claude n'est pas cité explicitement. — [GitHub](https://github.com/openai/openai-agents-python)
- `huggingface/smolagents` : https://github.com/huggingface/smolagents. Environ 30,4k étoiles, Apache-2.0. « a barebones library for agents that think in code ». — [GitHub](https://github.com/huggingface/smolagents)
- `pydantic/pydantic-ai` : https://github.com/pydantic/pydantic-ai. Environ 21,3k étoiles, MIT. Framework d'agents typé, multi-modèles. — [GitHub](https://github.com/pydantic/pydantic-ai)
- `n8n-io/n8n` : https://github.com/n8n-io/n8n. Environ 211k étoiles. Licence **« fair-code », Sustainable Use License** (plus une Enterprise License), donc **pas une licence OSI**. Auto-hébergeable avec Docker (port 5678). Plus de 400 intégrations selon la barre latérale, plus de 1500 selon le README (le dépôt se contredit). — [GitHub](https://github.com/n8n-io/n8n)
- `microsoft/agent-framework` : la page a renvoyé une erreur 404 lors de la vérification. Non vérifié (URL peut-être différente).

### Inferences
- Pour un créateur solo qui « utilise surtout Claude », une pile purement Anthropic (Claude Code, des sous-agents `.claude/agents` par métier, des Skills, des serveurs MCP) évite d'apprendre un framework en plus. Le Claude Agent SDK sert ensuite à faire tourner ces mêmes agents sans surveillance (scripts, CRON, CI).
- n8n est utile pour les flux planifiés et sans code (par ex. vidéo prête → upload YouTube/TikTok → notification), à condition d'accepter sa licence fair-code. Un usage interne est en principe permis, mais cela reste à vérifier dans le texte de la licence.
- CrewAI, avec ses rôles, est le framework tiers le plus proche du modèle « équipe d'agents » demandé. LangGraph offre plus de contrôle, mais il est plus complexe à prendre en main.
- AutoGen est à éviter (archivé). Si l'approche AutoGen plaît, AG2 est son fork actif, mais avec une base d'utilisateurs bien plus petite.

### Gaps
- Dates exactes du dernier commit ou de la dernière release pour LangGraph, CrewAI, OpenAI Agents SDK, smolagents, Pydantic AI, n8n et AG2 : la page GitHub ne les affichait pas et l'API était bloquée.
- Licence exacte de `claude-agent-sdk-typescript` non affichée.
- Microsoft Agent Framework : URL du dépôt non confirmée (404).
- Google ADK et Mastra n'ont pas été vérifiés.

## 2. Écosystème Claude Code : skills, sous-agents, commandes, hooks, marketplaces

### Takeaway
Les sources les plus fiables sont celles d'Anthropic : **anthropics/skills**, **claude-plugins-official** (marketplace gérée par Anthropic) et **claude-code**. Côté communauté, les références les plus citées sont **obra/superpowers**, **hesreallyhim/awesome-claude-code**, **wshobson/agents**, **VoltAgent/awesome-claude-code-subagents** et **davila7/claude-code-templates**. Il y a aussi des serveurs MCP utiles au game design (Blender, Unity).

### Cited Findings
**Officiel**
- `anthropics/skills` : https://github.com/anthropics/skills. Environ 197k étoiles, mis à jour le 16/11/2026. Pas de licence globale : beaucoup de skills sont sous Apache-2.0, dont docx, pdf, pptx et xlsx. Le README précise que ces skills sont « for demonstration and educational purposes only ». Le format est un dossier contenant un `SKILL.md` avec un frontmatter YAML (name, description). Le standard est décrit sur agentskills.io. — [GitHub](https://github.com/anthropics/skills); [Org](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-code` : environ 156k étoiles, mis à jour le 19/11/2026. — [Org](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-plugins-official` : https://github.com/anthropics/claude-plugins-official. Environ 47,7k étoiles, Apache-2.0 (chaque plugin peut avoir sa propre licence), mis à jour le 19/11/2026. Installation : `/plugin install {nom}@claude-plugins-official`, ou `/plugin > Discover` pour parcourir. Le README avertit : « Anthropic does not control what MCP servers, files, or other software are included in plugins and cannot verify that they will work as intended or that they won't change. » — [GitHub](https://github.com/anthropics/claude-plugins-official)
- `anthropics/claude-plugins-community` : environ 4,9k étoiles, Apache-2.0, mis à jour le 16/11/2026. Miroir en lecture seule de la marketplace communautaire. `anthropics/knowledge-work-plugins` : environ 37k étoiles, Apache-2.0, plugins pour Claude Cowork. — [Org](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-code-action` (10k, MIT, 19/11/2026) : Claude dans GitHub Actions. `anthropics/claude-code-security-review` (7k, MIT, 11/02/2026) : action GitHub de revue de sécurité. — [Org](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)

**Communauté**
- `obra/superpowers` : https://github.com/obra/superpowers. Environ 322k étoiles, MIT. « An agentic skills framework & software development methodology ». Il est installable depuis la marketplace officielle : `/plugin install superpowers@claude-plugins-official`. — [GitHub](https://github.com/obra/superpowers)
- `hesreallyhim/awesome-claude-code` : https://github.com/hesreallyhim/awesome-claude-code. Environ 58,3k étoiles, licence non identifiée sur la page, 2 430 commits. Liste de skills, agents, status lines, outils et plugins. Le dépôt n'explique pas comment les ressources listées sont vérifiées. — [GitHub](https://github.com/hesreallyhim/awesome-claude-code)
- `wshobson/agents` : https://github.com/wshobson/agents. Environ 42,7k étoiles, MIT. Il contient 93 plugins, 199 agents, 185 skills et 103 commandes. Installation : `/plugin marketplace add wshobson/agents`. Il est aussi compatible avec Codex, Cursor, etc. — [GitHub](https://github.com/wshobson/agents)
- `VoltAgent/awesome-claude-code-subagents` : https://github.com/VoltAgent/awesome-claude-code-subagents. Environ 26,7k étoiles, MIT. Il annonce plus de 161 sous-agents en 10 catégories, dont « Business & Product » et « Research & Analysis ». La section About dit « 100+ », ce qui est incohérent. — [GitHub](https://github.com/VoltAgent/awesome-claude-code-subagents)
- `davila7/claude-code-templates` : https://github.com/davila7/claude-code-templates. Environ 34k étoiles, MIT. CLI et registre d'environ 1 980 composants (918 skills, 422 agents, 288 commandes, 119 MCP, 63 hooks…). Installation : `npx claude-code-templates@latest`. — [GitHub](https://github.com/davila7/claude-code-templates)
- `punkpeye/awesome-mcp-servers` : https://github.com/punkpeye/awesome-mcp-servers. Environ 98,2k étoiles, MIT. Liste de serveurs MCP liée au répertoire glama.ai. — [GitHub](https://github.com/punkpeye/awesome-mcp-servers)
- Tendances du topic claude-code (non évaluées, à prendre avec prudence) : `thedotmack/claude-mem` (118k, mémoire persistante entre sessions), `addyosmani/agent-skills` (119k), `nextlevelbuilder/ui-ux-pro-max-skill` (152k), `heygen-com/hyperframes` (86,7k, « AI video you can actually edit », potentiellement utile au montage vidéo), `ruvnet/ruflo` (82,1k, orchestration d'essaims d'agents). — [Topic claude-code](https://github.com/topics/claude-code); [Topic ai-agents](https://github.com/topics/ai-agents)

**MCP utiles pour les métiers visés**
- `ahujasid/blender-mcp` : https://github.com/ahujasid/blender-mcp. Environ 35k étoiles, MIT. Pilote Blender par LLM. Projet non affilié à la Blender Foundation. Le serveur socket n'a **ni authentification ni chiffrement** (« anyone who can reach that port can run Python inside Blender »), l'outil `execute_blender_code` exécute du Python arbitraire, la télémétrie anonyme est activée par défaut (`DISABLE_TELEMETRY=true` pour la couper) et le mode sûr est désactivé par défaut. — [GitHub](https://github.com/ahujasid/blender-mcp)
- `CoplayDev/unity-mcp` : https://github.com/CoplayDev/unity-mcp. Environ 16,1k étoiles, MIT. Relie Claude à l'éditeur Unity (assets, scènes, scripts). — [GitHub](https://github.com/CoplayDev/unity-mcp)

### Inferences
- Ordre de confiance conseillé : (1) skills et plugins Anthropic, (2) plugins de `claude-plugins-official`, dont superpowers, (3) collections communautaires très suivies (wshobson, VoltAgent, claude-code-templates), à lire avant d'installer, (4) tout le reste.
- Pour une « équipe » (game design, montage, publication, sortie sur les stores, étude de marché), le plus robuste est d'écrire ses propres sous-agents dans `.claude/agents/` en s'inspirant de ces collections (par ex. la catégorie Business & Product de VoltAgent), plutôt que d'installer des centaines d'agents en bloc.
- Les étoiles des dépôts tendance de 2026 sont anormalement élevées (plusieurs centaines de milliers). Mieux vaut juger un dépôt sur son auteur, son historique, le nombre de contributeurs et le contenu de son code.

### Gaps
- Aucun MCP spécifique vérifié pour YouTube, TikTok, App Store Connect ou Google Play Console, ni pour Godot (le README d'awesome-mcp-servers n'a pas été lu en entier).
- Dates de dernier commit des dépôts communautaires non affichées.
- La licence d'awesome-claude-code n'est pas identifiée.

## 3. Ressources de prompt engineering reconnues

### Takeaway
Les références les plus sûres sont le tutoriel interactif d'Anthropic, ses cours (archivés mais encore lisibles), les cookbooks, et le Prompt Engineering Guide de DAIR.AI.

### Cited Findings
- `anthropics/prompt-eng-interactive-tutorial` : environ 40k étoiles, pas de licence affichée, mis à jour le 28/08/2026. Tutoriel interactif de prompt engineering. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/courses` : environ 23k étoiles, licence « Other », **archivé**, mis à jour le 28/08/2026. Cours éducatifs. — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `anthropics/claude-cookbooks` : environ 55k étoiles, MIT (voir section 1). — [Org Anthropic](https://github.com/orgs/anthropics/repositories?q=&type=all&sort=stargazers)
- `dair-ai/Prompt-Engineering-Guide` : https://github.com/dair-ai/Prompt-Engineering-Guide. Environ 80,2k étoiles, MIT. Guides, articles et notebooks sur le prompt engineering, le context engineering, le RAG et les agents. — [GitHub](https://github.com/dair-ai/Prompt-Engineering-Guide)

### Inferences
- Le tutoriel interactif reste la meilleure porte d'entrée pour Claude. Le dépôt `courses` est figé : contenu utile, mais il ne sera plus mis à jour.

### Gaps
- La « prompt library » d'Anthropic, en ligne sur docs.claude.com, n'a pas été vérifiée lors de cette passe.
- `f/awesome-chatgpt-prompts` n'a pas été vérifié.

## 4. Sécurité : risques des skills et MCP tiers, et comment les vérifier

### Takeaway
Les skills et serveurs MCP tiers sont une vraie chaîne d'approvisionnement à risque : des audits de 2026 trouvent des skills malveillants et des fuites d'identifiants en nombre important. Anthropic ne fait aucun audit de sécurité des MCP ni des plugins tiers. Il faut lire le code, épingler les versions, isoler l'exécution (sandbox ou VM) et scanner avec un outil dédié.

### Cited Findings
- La documentation Claude Code dit : « We encourage either writing your own MCP servers or using MCP servers from providers that you trust… Anthropic reviews connectors against its listing criteria… but does not security-audit or manage any MCP server. » — [Claude Code Security](https://code.claude.com/docs/en/security)
- Selon la même doc, des plugins peuvent ajouter des serveurs MCP, donc relire `.mcp.json` ne montre pas tous les serveurs chargés. Un dossier de projet non approuvé déclenche une demande de confiance, mais une session `-p` (headless) n'affiche ni la demande de confiance ni l'approbation MCP. — [Claude Code Security](https://code.claude.com/docs/en/security)
- Bonnes pratiques officielles : relire les commandes, ne pas envoyer de contenu non fiable directement à Claude, utiliser des VM pour les scripts et les appels à des services web externes, activer la sandbox (`/sandbox`, isolation des fichiers et du réseau), auditer `/permissions`, utiliser un dev container ou sandbox-runtime. — [Claude Code Security](https://code.claude.com/docs/en/security)
- La marketplace officielle avertit elle-même qu'Anthropic ne contrôle pas le contenu des plugins et ne peut pas garantir qu'ils ne changeront pas. — [claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
- Audit Snyk « ToxicSkills » : sur 3 984 skills, 36,82 % ont au moins une faille, 13,4 % une faille critique, et 76 contiennent une charge malveillante confirmée. 91 % des skills malveillants combinent malware et prompt injection. — [Snyk](https://snyk.io/fr/articles/skill-md-shell-access/) (chiffres repris du résumé de recherche, article non lu en entier)
- Registre ClawHub (OpenClaw) : 341 skills malveillants sur 2 857 (environ 12 %), campagne « ClawHavoc ». — [Tencent](https://matrix.tencent.com/en/2026/04/24/we-scanned-50000-skills-the-threat-persists); [Help Net Security](https://helpnetsecurity.com/2026/05/05/ai-agent-security-skills-blind-spots) (non lus en entier)
- Études universitaires citées : 1 899 serveurs MCP open source, dont 7,2 % ont des vulnérabilités générales et 5,5 % du tool poisoning (arXiv:2506.13538). 40,55 % des serveurs MCP distants exposent des outils sans authentification (arXiv:2605.22333). 1 708 problèmes de fuite d'identifiants dans 520 skills vulnérables sur 17 022 (arXiv:2604.03070). — résumé de recherche web pointant vers [obot.ai](https://obot.ai/blog/mcp-security-agent-skills-supply-chain/) et [securityscientist.net](https://www.securityscientist.net/blog/mcp-server-security/). Préprints non vérifiés directement, et définitions différentes d'une étude à l'autre.
- Outil de scan : `snyk/agent-scan`, anciennement Invariant Labs mcp-scan (l'URL `invariantlabs-ai/mcp-scan` y mène). Environ 3,3k étoiles, Apache-2.0. Il détecte les agents, MCP et skills installés et les scanne pour : prompt injection, tool poisoning, « toxic flows », malware caché en langage naturel, mauvaise gestion des identifiants. — [GitHub](https://github.com/invariantlabs-ai/mcp-scan)
- Exemple concret : blender-mcp n'a pas d'authentification et exécute du Python arbitraire (voir section 2). — [GitHub](https://github.com/ahujasid/blender-mcp)

### Inferences
Liste de vérification proposée pour un créateur solo :
1. Préférer les sources officielles (Anthropic, `modelcontextprotocol/servers`, éditeurs connus comme `github/github-mcp-server`).
2. Lire chaque `SKILL.md`, ses scripts et ses hooks avant d'installer : chercher `curl | sh`, du base64, des appels réseau inattendus et des lectures de `~/.ssh`, `.env` ou des trousseaux.
3. Épingler une version ou un commit, et ne pas activer les mises à jour automatiques de plugins tiers.
4. Ne jamais donner aux agents de publication (YouTube, App Store, Google Play) des identifiants à large portée. Utiliser des tokens à portée minimale, stockés hors du dépôt, et exiger une validation humaine avant tout envoi ou publication.
5. Lancer `snyk/agent-scan` sur la configuration locale, activer `/sandbox`, garder les MCP locaux (Blender, Unity) sur localhost.
6. Se méfier des étoiles gonflées et des dépôts tendance récents.

### Gaps
- Pas d'audit public trouvé portant spécifiquement sur `claude-plugins-official` ou sur les grandes collections communautaires (wshobson, VoltAgent, claude-code-templates).
- Les chiffres Snyk, Tencent et des préprints viennent d'un résumé de recherche web : les sources primaires n'ont pas été lues en entier.
