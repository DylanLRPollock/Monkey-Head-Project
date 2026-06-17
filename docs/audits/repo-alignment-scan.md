# Repository Alignment Scan

This file lists terms and paths that may need alignment with the current project direction.


## docker

.editorconfig:134:# Dockerfiles
.editorconfig:135:[{Dockerfile,**/Dockerfile,*.[Dd]ockerfile}]
.gitattributes:33:Dockerfile     text eol=lf
.gitattributes:34:docker-compose*.yml text eol=lf
.github/ISSUE_TEMPLATE/bug_report.yml:41:        - Docker
.migration/inventory/git-ls-files.pass-01.txt:7:.dockerignore
.migration/inventory/git-ls-files.pass-01.txt:58:infra/docker/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:59:infra/docker/Dockerfile.vnc
.migration/inventory/git-ls-files.pass-01.txt:60:infra/docker/docker-compose.yml
.migration/inventory/git-ls-files.pass-01.txt:61:infra/docker/docker/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:62:infra/docker/docker/docker-compose.yml
.migration/inventory/git-ls-files.pass-01.txt:63:infra/docker/docker/hostos/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:64:infra/docker/docker/hostos/hostos.py
.migration/inventory/git-ls-files.pass-01.txt:65:infra/docker/docker/hostos/hostos.yaml
.migration/inventory/git-ls-files.pass-01.txt:66:infra/docker/docker/hostos/requirements.txt
.migration/inventory/git-ls-files.pass-01.txt:67:infra/docker/docker/nanoos/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:68:infra/docker/docker/nanoos/nanoos.py
.migration/inventory/git-ls-files.pass-01.txt:69:infra/docker/docker/nanoos/nanoos.yaml
.migration/inventory/git-ls-files.pass-01.txt:70:infra/docker/docker/nanoos/requirements.txt
.migration/inventory/git-ls-files.pass-01.txt:71:infra/docker/docker/orchestrator_utils.py
.migration/inventory/git-ls-files.pass-01.txt:72:infra/docker/docker/pygpt/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:73:infra/docker/docker/subos/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:74:infra/docker/docker/subos/requirements.txt
.migration/inventory/git-ls-files.pass-01.txt:75:infra/docker/docker/subos/subos.py
.migration/inventory/git-ls-files.pass-01.txt:76:infra/docker/docker/subos/subos.yaml
.migration/inventory/git-ls-files.pass-01.txt:941:src/huey/memory/DOCKER/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:942:src/huey/memory/DOCKER/Dockerfile.vnc
.migration/inventory/git-ls-files.pass-01.txt:1031:src/huey/memory/PDF/Building an Expandable, Modular Cloud OS with Docker and Kubernetes.pdf
.migration/inventory/git-ls-files.pass-01.txt:1037:src/huey/memory/PDF/Configuring Docker & Kubernetes Networking on macOS for Direct Ethernet Access.pdf
.migration/inventory/git-ls-files.pass-01.txt:1045:src/huey/memory/PDF/Gordon_ A Context-Aware AI Chatbot for Docker Developer Assistance.pdf
.migration/inventory/git-ls-files.pass-01.txt:1215:src/huey/memory/SH/docker_cleanup.sh
.migration/inventory/git-ls-files.pass-01.txt:1216:src/huey/memory/SH/docker_dev_setup.sh
.migration/inventory/git-ls-files.pass-01.txt:1217:src/huey/memory/SH/docker_setup.sh
.migration/inventory/git-ls-files.pass-01.txt:1264:src/huey/memory/YML/docker-compose.yml
.security/bandit-baseline.json:3417:      "code": "64     logger.info(\"Building Huey Docker image %s from %s...\", tag, context)\n65     build = subprocess.run(\n66         [\"docker\", \"build\", \"-t\", tag, context],\n67         stdout=subprocess.PIPE,\n68         stderr=subprocess.PIPE,\n69     )\n70     check_error(build, \"Build Huey Docker Image\")\n",
.security/bandit-baseline.json:3441:      "code": "64     logger.info(\"Building Huey Docker image %s from %s...\", tag, context)\n65     build = subprocess.run(\n66         [\"docker\", \"build\", \"-t\", tag, context],\n67         stdout=subprocess.PIPE,\n68         stderr=subprocess.PIPE,\n69     )\n70     check_error(build, \"Build Huey Docker Image\")\n",
.security/bandit-baseline.json:3465:      "code": "80     os.chdir(workdir)\n81     deploy = subprocess.run(\n82         [\"docker-compose\", \"-f\", compose_file, \"up\", \"-d\"],\n83         stdout=subprocess.PIPE,\n84         stderr=subprocess.PIPE,\n85     )\n86     check_error(deploy, \"Huey Deployment\")\n",
.security/bandit-baseline.json:3489:      "code": "80     os.chdir(workdir)\n81     deploy = subprocess.run(\n82         [\"docker-compose\", \"-f\", compose_file, \"up\", \"-d\"],\n83         stdout=subprocess.PIPE,\n84         stderr=subprocess.PIPE,\n85     )\n86     check_error(deploy, \"Huey Deployment\")\n",
.security/bandit-baseline.json:3853:      "code": "25     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n26     start_containers = subprocess.run(\n27         [\"docker-compose\", \"up\", \"-d\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n28     )\n29     check_error(start_containers, \"Start Docker Containers\")\n",
.security/bandit-baseline.json:3875:      "code": "25     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n26     start_containers = subprocess.run(\n27         [\"docker-compose\", \"up\", \"-d\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n28     )\n29     check_error(start_containers, \"Start Docker Containers\")\n",
.security/bandit-baseline.json:3897:      "code": "30 \n31     list_containers = subprocess.run(\n32         [\"docker\", \"ps\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n33     )\n34     check_error(list_containers, \"List Running Containers\")\n",
.security/bandit-baseline.json:3919:      "code": "30 \n31     list_containers = subprocess.run(\n32         [\"docker\", \"ps\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n33     )\n34     check_error(list_containers, \"List Running Containers\")\n",
.security/bandit-baseline.json:3941:      "code": "38     logger.info(\"Managing Volumes...\")\n39     list_volumes = subprocess.run(\n40         [\"docker\", \"volume\", \"ls\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n41     )\n42     check_error(list_volumes, \"List Docker Volumes\")\n",
.security/bandit-baseline.json:3963:      "code": "38     logger.info(\"Managing Volumes...\")\n39     list_volumes = subprocess.run(\n40         [\"docker\", \"volume\", \"ls\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n41     )\n42     check_error(list_volumes, \"List Docker Volumes\")\n",
.security/bandit-baseline.json:3985:      "code": "43 \n44     prune_volumes = subprocess.run(\n45         [\"docker\", \"volume\", \"prune\", \"-f\"],\n46         stdout=subprocess.PIPE,\n47         stderr=subprocess.PIPE,\n48     )\n49     check_error(prune_volumes, \"Prune Docker Volumes\")\n",
.security/bandit-baseline.json:4009:      "code": "43 \n44     prune_volumes = subprocess.run(\n45         [\"docker\", \"volume\", \"prune\", \"-f\"],\n46         stdout=subprocess.PIPE,\n47         stderr=subprocess.PIPE,\n48     )\n49     check_error(prune_volumes, \"Prune Docker Volumes\")\n",
.security/bandit-baseline.json:4357:      "code": "122     logger.info(\"Building Docker image %s...\", tag)\n123     build = subprocess.run(\n124         [\"docker\", \"build\", \"-t\", tag, \".\"],\n125         stdout=subprocess.PIPE,\n126         stderr=subprocess.PIPE,\n127     )\n128     check_error(build, \"Build Docker Image\")\n",
.security/bandit-baseline.json:4381:      "code": "122     logger.info(\"Building Docker image %s...\", tag)\n123     build = subprocess.run(\n124         [\"docker\", \"build\", \"-t\", tag, \".\"],\n125         stdout=subprocess.PIPE,\n126         stderr=subprocess.PIPE,\n127     )\n128     check_error(build, \"Build Docker Image\")\n",
.security/bandit-baseline.json:4405:      "code": "134     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n135     stop = subprocess.run(\n136         [\"docker-compose\", \"down\"],\n137         stdout=subprocess.PIPE,\n138         stderr=subprocess.PIPE,\n139     )\n140     check_error(stop, \"Stop Docker Containers\")\n",
.security/bandit-baseline.json:4429:      "code": "134     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n135     stop = subprocess.run(\n136         [\"docker-compose\", \"down\"],\n137         stdout=subprocess.PIPE,\n138         stderr=subprocess.PIPE,\n139     )\n140     check_error(stop, \"Stop Docker Containers\")\n",
.security/bandit-baseline.json:4453:      "code": "145     logger.info(\"Pruning unused Docker images...\")\n146     prune_images = subprocess.run(\n147         [\"docker\", \"image\", \"prune\", \"-f\"],\n148         stdout=subprocess.PIPE,\n149         stderr=subprocess.PIPE,\n150     )\n151     check_error(prune_images, \"Prune Docker Images\")\n",
.security/bandit-baseline.json:4477:      "code": "145     logger.info(\"Pruning unused Docker images...\")\n146     prune_images = subprocess.run(\n147         [\"docker\", \"image\", \"prune\", \"-f\"],\n148         stdout=subprocess.PIPE,\n149         stderr=subprocess.PIPE,\n150     )\n151     check_error(prune_images, \"Prune Docker Images\")\n",
.security/bandit-baseline.json:4501:      "code": "156     logger.info(\"Managing Docker networks...\")\n157     list_networks = subprocess.run(\n158         [\"docker\", \"network\", \"ls\"],\n159         stdout=subprocess.PIPE,\n160         stderr=subprocess.PIPE,\n161     )\n162     check_error(list_networks, \"List Docker Networks\")\n",
.security/bandit-baseline.json:4525:      "code": "156     logger.info(\"Managing Docker networks...\")\n157     list_networks = subprocess.run(\n158         [\"docker\", \"network\", \"ls\"],\n159         stdout=subprocess.PIPE,\n160         stderr=subprocess.PIPE,\n161     )\n162     check_error(list_networks, \"List Docker Networks\")\n",
.security/bandit-baseline.json:4549:      "code": "163 \n164     prune_networks = subprocess.run(\n165         [\"docker\", \"network\", \"prune\", \"-f\"],\n166         stdout=subprocess.PIPE,\n167         stderr=subprocess.PIPE,\n168     )\n169     check_error(prune_networks, \"Prune Docker Networks\")\n",
.security/bandit-baseline.json:4573:      "code": "163 \n164     prune_networks = subprocess.run(\n165         [\"docker\", \"network\", \"prune\", \"-f\"],\n166         stdout=subprocess.PIPE,\n167         stderr=subprocess.PIPE,\n168     )\n169     check_error(prune_networks, \"Prune Docker Networks\")\n",
.security/bandit-baseline.json:4597:      "code": "174     logger.info(\"Listing running containers...\")\n175     list_containers_cmd = subprocess.run(\n176         [\"docker\", \"ps\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n177     )\n178     check_error(list_containers_cmd, \"List Docker Containers\")\n",
.security/bandit-baseline.json:4619:      "code": "174     logger.info(\"Listing running containers...\")\n175     list_containers_cmd = subprocess.run(\n176         [\"docker\", \"ps\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n177     )\n178     check_error(list_containers_cmd, \"List Docker Containers\")\n",
.security/bandit-baseline.json:4641:      "code": "184     logger.info(\"Fetching logs for container %s...\", container_name)\n185     logs = subprocess.run(\n186         [\"docker\", \"logs\", container_name],\n187         stdout=subprocess.PIPE,\n188         stderr=subprocess.PIPE,\n189     )\n190     check_error(logs, \"Get Container Logs\")\n",
.security/bandit-baseline.json:4665:      "code": "184     logger.info(\"Fetching logs for container %s...\", container_name)\n185     logs = subprocess.run(\n186         [\"docker\", \"logs\", container_name],\n187         stdout=subprocess.PIPE,\n188         stderr=subprocess.PIPE,\n189     )\n190     check_error(logs, \"Get Container Logs\")\n",
.security/bandit-baseline.json:5161:      "code": "33     logger.info(\"Installing additional tools...\")\n34     additional_tools_install = subprocess.run(\n35         [\"apt-get\", \"install\", \"-y\", \"python3\", \"python3-venv\", \"docker.io\"],\n36         stdout=subprocess.PIPE,\n37         stderr=subprocess.PIPE,\n38     )\n39     check_error(additional_tools_install, \"Additional Tools Installation\")\n",
.security/bandit-baseline.json:5185:      "code": "33     logger.info(\"Installing additional tools...\")\n34     additional_tools_install = subprocess.run(\n35         [\"apt-get\", \"install\", \"-y\", \"python3\", \"python3-venv\", \"docker.io\"],\n36         stdout=subprocess.PIPE,\n37         stderr=subprocess.PIPE,\n38     )\n39     check_error(additional_tools_install, \"Additional Tools Installation\")\n",
CHANGELOG.md:22:- Docker alignment documented for v101.1 with HueyOS runtime expectations (`huey-api`, non-root `hueyos`, repository package install) instead of PyGPT as primary runtime.
README.md:1011:- PyHuey stays optional cockpit/tooling (`infra/docker/pyhuey`) and is not the HueyOS/Huey Brain runtime path.
README.md:1021:Environment guidance for Docker/Compose:
SECURITY.md:72:* Running HueyOS in containers (Docker/Podman) or VMs (KVM/VirtualBox) is supported **as long as** the underlying host matches the OS/arch/kernel assumptions above.
SECURITY.md:73:* Container images and `docker-compose` files provided in this repository are **in scope**. Host misconfiguration outside documented recommendations is not.
SECURITY.md:103:  * Relevant configuration (`huey.env`, `docker-compose.yml`, systemd units), with secrets redacted.
SECURITY.md:226:In some cases, we may first ship **configuration-only mitigations** or documentation updates (tightening sample `docker-compose` defaults, recommended firewall rules, etc.) ahead of a full patch if that meaningfully reduces risk quickly.
SECURITY.md:251:  * Example Dockerfiles, `docker-compose.yml`, and related infrastructure definitions
SECURITY.md:347:  * Secure-by-default sample configs (`huey.env.example`, `docker-compose.yml`, systemd units)
audit-requirements.txt:151:docker==7.1.0
docs/_build/html/_sources/security/security-hardening-status.md.txt:24:- A Docker image policy document exists to support image provenance and pinning practices.
docs/_build/html/_sources/security/security-hardening-status.md.txt:39:- Re-check Docker base image digests and upstream CVEs at each release cycle.
docs/_build/html/_sources/security/security-hardening-status.md.txt:133:## Docker image pinning policy
docs/_build/html/_sources/security/security-hardening-status.md.txt:141:- Keep dev, staging, and production Dockerfiles aligned on pinning strategy; environment differences should be explicit and justified.
docs/_build/html/index.html:50:<li class="toctree-l2"><a class="reference internal" href="security/security-hardening-status.html#docker-image-pinning-policy">Docker image pinning policy</a></li>
docs/_build/html/searchindex.js:1:Search.setIndex({"alltitles":{"1) pip-audit (Python dependency vulnerabilities)":[[3,"pip-audit-python-dependency-vulnerabilities"]],"2) Bandit (Python static security linting)":[[3,"bandit-python-static-security-linting"]],"3) Secret scanning":[[3,"secret-scanning"]],"Compatibility-path decision":[[0,"compatibility-path-decision"]],"Core Docs":[[2,null]],"Docker image pinning policy":[[3,"docker-image-pinning-policy"]],"Environment-specific guidance":[[3,"environment-specific-guidance"]],"Local security checks":[[3,"local-security-checks"]],"Monkey-Head-Project Documentation":[[2,null]],"Providing development secrets safely":[[3,"providing-development-secrets-safely"]],"Resolved hardening items":[[3,"resolved-hardening-items"]],"Runtime impact":[[0,"runtime-impact"]],"Scope and intent":[[3,"scope-and-intent"]],"Security Hardening Status":[[3,null]],"Status disclaimer":[[3,"status-disclaimer"]],"Summary of metadata-only changes":[[0,"summary-of-metadata-only-changes"]],"Token requirements by environment":[[3,"token-requirements-by-environment"]],"Unresolved or manual hardening items":[[3,"unresolved-or-manual-hardening-items"]],"VNC/noVNC safe access pattern":[[3,"vnc-novnc-safe-access-pattern"]],"v101.1 Namespace Migration Direction":[[1,null]],"v101.1 repo-control path cleanup":[[0,null]],"\u201cDo not commit\u201d list":[[3,"do-not-commit-list"]]},"docnames":["audits/v101.1-repo-control-paths","development/v101.1-namespace-migration","index","security/security-hardening-status"],"envversion":{"sphinx":65,"sphinx.domains.c":3,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":9,"sphinx.domains.index":1,"sphinx.domains.javascript":3,"sphinx.domains.math":2,"sphinx.domains.python":4,"sphinx.domains.rst":2,"sphinx.domains.std":2},"filenames":["audits\\v101.1-repo-control-paths.md","development\\v101.1-namespace-migration.md","index.rst","security\\security-hardening-status.md"],"indexentries":{},"objects":{},"objnames":{},"objtypes":{},"terms":{"03":3,"05":[0,3],"1":2,"11":0,"2026":[0,3],"A":3,"If":3,"It":3,"No":[0,1,3],"The":3,"These":3,"accept":3,"access":2,"accident":3,"action":3,"activ":[0,3],"ad":3,"add":1,"addit":3,"address":3,"adjac":3,"affect":3,"again":3,"against":3,"align":3,"alon":3,"alreadi":0,"altern":3,"an":3,"ani":3,"anomali":3,"api":[0,1,3],"app":3,"appli":3,"appropri":3,"approv":3,"ar":3,"artifact":3,"attempt":3,"auth":3,"authent":3,"avoid":3,"back":3,"base":3,"baselin":3,"bastion":3,"bearer":3,"becaus":0,"befor":3,"behavior":1,"block":3,"bootstrap":3,"bound":3,"break":3,"build":3,"cadenc":3,"canon":1,"capabl":3,"central":3,"chang":[1,2,3],"check":2,"ci":3,"cleanup":2,"cli":1,"code":[0,1,3],"codeown":0,"commit":2,"compat":[1,2],"complet":3,"compromis":3,"config":3,"confirm":[0,3],"connect":3,"consid":3,"consist":3,"contain":3,"context":3,"continu":3,"control":[2,3],"core":1,"coverag":3,"credenti":3,"critic":3,"current":3,"cve":3,"cycl":3,"data":3,"date":0,"debug":3,"decis":2,"declar":3,"dedic":3,"defens":3,"deploy":3,"depth":3,"detect":3,"dev":3,"develop":2,"differ":3,"digest":3,"direct":2,"directli":3,"directori":0,"disabl":3,"disclaim":2,"dist":3,"distribut":1,"do":2,"doc":3,"docker":2,"dockerfil":3,"document":[0,1,3],"doe":[0,1,3],"dump":3,"dure":1,"each":3,"empti":1,"enforc":3,"env":3,"environ":2,"ephemer":3,"equival":3,"establish":1,"everi":3,"evolv":3,"exampl":3,"except":3,"exclud":3,"exist":[0,1,3],"expect":3,"expir":3,"explicit":3,"explicitli":1,"export":3,"expos":3,"exposur":3,"featur":3,"file":[0,3],"firewal":3,"float":3,"follow":3,"format":3,"from":[0,3],"front":3,"full":3,"gate":3,"gatewai":3,"gener":3,"gitattribut":0,"github":0,"gitignor":3,"gitleak":3,"gitmodul":0,"glass":3,"gpt":0,"group":3,"guardrail":3,"gui":3,"guidanc":2,"ha":1,"handl":3,"hard":3,"harden":2,"high":3,"higher":3,"histori":3,"hoc":3,"hook":3,"hsm":3,"huei":[0,1],"hueyo":[1,2],"i":[0,1,3],"ident":3,"imag":2,"immedi":3,"immut":3,"impact":2,"implement":[1,3],"import":1,"incid":3,"includ":3,"infrastructur":3,"ingress":3,"inject":3,"input":3,"instal":3,"integr":[0,2,3],"intent":2,"internet":3,"introduc":3,"ip":3,"isol":3,"item":2,"json":3,"justifi":3,"keep":3,"kei":3,"keychain":3,"last":3,"layer":3,"layout":3,"leak":3,"leakag":3,"least":3,"legaci":1,"like":3,"linguist":0,"list":2,"live":3,"local":2,"locat":0,"lockfil":3,"log":3,"long":3,"lowest":3,"m":3,"maintain":[1,3],"mainten":3,"manag":3,"mandatori":3,"manual":2,"match":[0,3],"mean":3,"memori":1,"merg":3,"metadata":[2,3],"mfa":3,"migrat":2,"minim":3,"mirror":3,"moder":3,"modul":1,"monitor":3,"move":1,"must":3,"namespac":2,"nano":0,"need":3,"network":3,"never":3,"new":3,"non":3,"note":3,"novnc":2,"one":3,"ongo":3,"onli":[2,3],"open":3,"oper":3,"out":3,"output":3,"ownership":0,"packag":1,"password":3,"patch":3,"path":[2,3],"pattern":2,"period":3,"perman":3,"pick":3,"pin":2,"placehold":3,"plaintext":3,"plane":3,"point":0,"polici":2,"port":3,"possibl":3,"postur":3,"pr":3,"practic":3,"pre":3,"prefer":3,"present":3,"preserv":1,"privat":3,"privileg":3,"prod":3,"product":3,"prohibit":3,"project":3,"proven":3,"provid":2,"public":3,"purpos":3,"py":[0,1],"pygpt":0,"pygpt_net":3,"pyhuei":[0,2],"python":0,"r":3,"rather":3,"re":3,"real":[0,3],"reassess":3,"rebuild":3,"recommend":3,"record":[1,3],"recur":3,"refer":3,"registri":3,"regular":3,"relat":3,"releas":3,"relev":3,"remain":[1,3],"remedi":3,"remot":3,"remov":[0,3],"repo":[2,3],"report":3,"repositori":[0,3],"resolv":2,"respons":3,"restrict":3,"retain":0,"review":3,"revisit":3,"revoc":3,"revok":3,"risk":3,"rotat":3,"rule":[0,3],"run":3,"runtim":[1,2,3],"safe":2,"sampl":3,"scaffold":1,"scanner":3,"schedul":3,"scope":[1,2],"screenshot":3,"secret":2,"secur":2,"sensit":3,"serv":3,"servic":3,"session":3,"share":3,"shell":3,"short":3,"should":3,"site":2,"so":0,"sourc":[0,3],"specif":2,"src":[0,1],"sso":3,"stage":3,"stale":0,"statu":2,"still":3,"strategi":3,"strict":3,"strong":3,"structur":3,"style":3,"subject":3,"submodul":0,"summari":2,"support":3,"surfac":[1,3],"tag":3,"task":[1,3],"templat":3,"temporari":3,"termin":3,"test":3,"than":3,"thei":3,"thi":[0,1,2,3],"threat":3,"time":[0,3],"tl":3,"toler":3,"track":3,"trail":3,"treat":3,"troubleshoot":3,"trust":3,"tune":3,"under":[1,3],"unless":3,"unresolv":2,"until":1,"up":3,"updat":[0,3],"upgrad":3,"upstream":3,"us":3,"user":3,"v101":2,"valid":3,"valu":3,"var":3,"variabl":3,"vendor":0,"venv":3,"verbos":3,"verif":3,"verifi":3,"version":3,"via":3,"vnc":2,"vpn":3,"wa":0,"were":0,"when":3,"whenev":3,"where":3,"while":3,"window":3,"work":[2,3],"workflow":3,"workload":3,"x":3,"you":3,"zero":3},"titles":["v101.1 repo-control path cleanup","v101.1 Namespace Migration Direction","Monkey-Head-Project Documentation","Security Hardening Status"],"titleterms":{"1":[0,1,3],"2":3,"3":3,"access":3,"audit":3,"bandit":3,"chang":0,"check":3,"cleanup":0,"commit":3,"compat":0,"control":0,"core":2,"decis":0,"depend":3,"develop":3,"direct":1,"disclaim":3,"do":3,"doc":2,"docker":3,"document":2,"environ":3,"guidanc":3,"harden":3,"head":2,"imag":3,"impact":0,"intent":3,"item":3,"lint":3,"list":3,"local":3,"manual":3,"metadata":0,"migrat":1,"monkei":2,"namespac":1,"novnc":3,"onli":0,"path":0,"pattern":3,"pin":3,"pip":3,"polici":3,"project":2,"provid":3,"python":3,"repo":0,"requir":3,"resolv":3,"runtim":0,"safe":3,"scan":3,"scope":3,"secret":3,"secur":3,"specif":3,"static":3,"statu":3,"summari":0,"token":3,"unresolv":3,"v101":[0,1],"vnc":3,"vulner":3}})
docs/_build/html/security/security-hardening-status.html:82:<li><p>A Docker image policy document exists to support image provenance and pinning practices.</p></li>
docs/_build/html/security/security-hardening-status.html:99:<li><p>Re-check Docker base image digests and upstream CVEs at each release cycle.</p></li>
docs/_build/html/security/security-hardening-status.html:204:<section id="docker-image-pinning-policy">
docs/_build/html/security/security-hardening-status.html:205:<h2>Docker image pinning policy<a class="headerlink" href="#docker-image-pinning-policy" title="Link to this heading">┬╢</a></h2>
docs/_build/html/security/security-hardening-status.html:212:<li><p>Keep dev, staging, and production Dockerfiles aligned on pinning strategy; environment differences should be explicit and justified.</p></li>
docs/_build/html/security/security-hardening-status.html:272:<li class="toctree-l2"><a class="reference internal" href="#docker-image-pinning-policy">Docker image pinning policy</a></li>
docs/audits/v101.1-dependency-source-of-truth.md:4:Scope: `pyproject.toml`, `requirements.txt`, `constraints.txt`, CI workflows, Dockerfiles.
docs/audits/v101.1-dependency-source-of-truth.md:16:- `infra/docker/Dockerfile`
docs/audits/v101.1-dependency-source-of-truth.md:17:- `infra/docker/pyhuey/Dockerfile`
docs/audits/v101.1-dependency-source-of-truth.md:18:- `infra/docker/docker/Dockerfile`
docs/audits/v101.1-dependency-source-of-truth.md:29:- Install surfaces used by CI and main Docker builds install from the package metadata (`pip install -e ".[dev]"` or `pip install .`/`pip install ".[extras]"), which resolves from `pyproject.toml`.
docs/audits/v101.1-dependency-source-of-truth.md:53:### 5) Docker install authority
docs/audits/v101.1-dependency-source-of-truth.md:57:- `infra/docker/Dockerfile` installs this repository package with optional extras (`pip install .` / `pip install ".[extras]"), so dependency source is `pyproject.toml`.
docs/audits/v101.1-dependency-source-of-truth.md:58:- `infra/docker/docker/Dockerfile` also installs this repository with extras from package metadata.
docs/audits/v101.1-dependency-source-of-truth.md:59:- `infra/docker/pyhuey/Dockerfile` intentionally installs `pygpt-net` directly for optional cockpit/provenance compatibility.
docs/audits/v101.1-dependency-source-of-truth.md:88:   - Docker HueyOS runtime builds: package metadata from `pyproject.toml`.
docs/audits/v101.1-dependency-source-of-truth.md:89:   - Docker optional PyHuey cockpit image: explicit `pygpt-net` install (separate intent).
docs/audits/v101.1-docker-alignment.md:1:# v101.1 Docker Alignment Audit
docs/audits/v101.1-docker-alignment.md:4:Align the main HueyOS Docker runtime with the repository package (`hueyos`) and remove PyGPT as the primary runtime.
docs/audits/v101.1-docker-alignment.md:10:docker compose -f infra/docker/docker-compose.yml build
docs/audits/v101.1-docker-alignment.md:16:HUEY_BUILD_EXTRAS=ml,data,cloud docker compose -f infra/docker/docker-compose.yml build
docs/audits/v101.1-docker-alignment.md:23:docker compose -f infra/docker/docker-compose.yml up -d api
docs/audits/v101.1-docker-alignment.md:29:docker compose -f infra/docker/docker-compose.yml --profile worker up -d worker
docs/audits/v101.1-docker-alignment.md:46:docker compose -f infra/docker/docker-compose.yml config
docs/audits/v101.1-docker-alignment.md:50:docker compose -f infra/docker/docker-compose.yml ps
docs/audits/v101.1-stabilization-final.md:18:- Evaluated Docker/Compose and PyHuey smoke-test requirement gates.
docs/audits/v101.1-stabilization-final.md:51:## Docker/Compose validation status
docs/audits/v101.1-stabilization-final.md:54:- Reason: this task did not modify Docker/Compose files, and there was no explicit Docker-change delta in this run to validate.
docs/audits/v101.1-stabilization-final.md:80:Only after those pass should Docker/Compose and PyHuey smoke gates be re-evaluated as release blockers for final stabilization sign-off.
docs/legal/provenance-and-licenses.md:28:- `infra/docker/pyhuey/README.md` states the PyHuey image is optional cockpit/tooling and separate from the main HueyOS runtime image.
docs/legal/provenance-and-licenses.md:36:- `infra/docker/pyhuey/README.md` explicitly says the cockpit image is derived from upstream `pygpt-net` for provenance/compatibility.
docs/security/docker-image-policy.md:1:# Docker Image Pinning & Update Policy
docs/security/docker-image-policy.md:3:This repository uses Docker images in both development and runtime workflows. To reduce supply-chain risk and avoid surprise breakage, follow these rules:
docs/security/docker-image-policy.md:33:- Any Dockerfile using `ARG DEBIAN_RELEASE=forky` or `ARG DEBIAN_VERSION=forky` must include a comment noting this is an intentional dev/testing default.
docs/security/security-concerns-and-fixes.md:13:     `infra/secrets/` from Docker build contexts.
docs/security/security-concerns-and-fixes.md:30:     `0.0.0.0` when Docker needs it.
docs/security/security-hardening-status.md:24:- A Docker image policy document exists to support image provenance and pinning practices.
docs/security/security-hardening-status.md:39:- Re-check Docker base image digests and upstream CVEs at each release cycle.
docs/security/security-hardening-status.md:133:## Docker image pinning policy
docs/security/security-hardening-status.md:141:- Keep dev, staging, and production Dockerfiles aligned on pinning strategy; environment differences should be explicit and justified.
docs/security/security-maintenance-audit.md:25:   - Docker Compose currently builds with `3.11-slim` by default.
docs/security/threat-model-v101.1.md:26:   - Runtime behavior inside Docker images vs. host privileges/mounts.
docs/security/threat-model-v101.1.md:49:2. **Dependency declarations and pins** in `pyproject.toml`, `requirements.txt`, and container Dockerfiles.
docs/security/tool_permission_boundaries.md:23:- `monkey.docker.stop`
docs/security/tool_permission_boundaries.md:24:- `monkey.docker.clean`
docs/unsorted/CONTRIBUTING.md:54:- Docker (optional) if you run sandboxed plugins or containers during tests
docs/unsorted/index.md:25:huey deploy --mode docker         # docker-only deployment
docs/unsorted/orchestrator-deployment.md:10:python3 docker/hostos/hostos.py --workspace "$HOME/HostOS" all
docs/unsorted/orchestrator-deployment.md:11:python3 docker/subos/subos.py --workspace "$HOME/SubOS" --service-port 8080 all
docs/unsorted/orchestrator-deployment.md:12:python3 docker/nanoos/nanoos.py --workspace "$HOME/NanoOS" --service-port 8081 all
docs/unsorted/repository-restructure-inventory.md:29:- `docker/` + `Dockerfile` + `Dockerfile.vnc` + `docker-compose.yml` ΓåÆ `infra/docker/`
docs/unsorted/repository-restructure-recommendation.md:28:Γöé   Γö£ΓöÇΓöÇ docker/              # all docker definitions and orchestration helpers
infra/docker/docker-compose.yml:20:      dockerfile: Dockerfile
infra/docker/docker-compose.yml:59:      dockerfile: pyhuey/Dockerfile
infra/docker/docker/Dockerfile:1:# syntax=docker/dockerfile:1.7
infra/docker/docker/docker-compose.yml:30:  # Windows L:\ bound into containers via Docker Desktop WSL path
infra/docker/docker/docker-compose.yml:52:      dockerfile: Dockerfile
infra/docker/docker/docker-compose.yml:108:      context: docker/subos
infra/docker/docker/docker-compose.yml:109:      dockerfile: Dockerfile
infra/docker/docker/docker-compose.yml:121:      context: docker/nanoos
infra/docker/docker/docker-compose.yml:122:      dockerfile: Dockerfile
infra/docker/docker/hostos/Dockerfile:1:# syntax=docker/dockerfile:1.7
infra/docker/docker/hostos/hostos.py:42:    "docker.io",
infra/docker/docker/hostos/hostos.py:43:    "docker-compose-plugin",  # provides `docker compose`
infra/docker/docker/hostos/hostos.py:69:        required_commands=("git", "docker", "kubectl"),
infra/docker/docker/hostos/hostos.py:82:    """Ensure Docker is ready for HostOS workloads."""
infra/docker/docker/hostos/hostos.py:106:    """Run docker compose and apply the HostOS manifest."""
infra/docker/docker/hostos/hostos.py:111:    compose_cmd = ["docker", "compose", "up", "-d"] if shutil.which("docker") else None
infra/docker/docker/hostos/hostos.py:114:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/hostos/hostos.py:115:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/hostos/hostos.py:117:        log.warning("Docker not found; skipping docker compose step.")
infra/docker/docker/hostos/hostos.py:157:    sub.add_parser("deploy", help="Run docker compose and apply hostos.yaml")
infra/docker/docker/hostos/hostos.py:180:    log.info("Done. You may need to log out/in for docker group to take effect.")
infra/docker/docker/hostos/requirements.txt:2:docker>=7.0.0
infra/docker/docker/nanoos/Dockerfile:1:# syntax=docker/dockerfile:1.7
infra/docker/docker/nanoos/nanoos.py:43:    "docker.io",
infra/docker/docker/nanoos/nanoos.py:44:    "docker-compose-plugin",
infra/docker/docker/nanoos/nanoos.py:64:        required_commands=("git", "docker"),
infra/docker/docker/nanoos/nanoos.py:82:    if shutil.which("docker"):
infra/docker/docker/nanoos/nanoos.py:83:        res = run(["docker", "compose", "up", "-d"], log, check=False)
infra/docker/docker/nanoos/nanoos.py:84:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/nanoos/nanoos.py:85:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/nanoos/nanoos.py:87:        log.warning("Docker not found; skipping docker compose step.")
infra/docker/docker/nanoos/requirements.txt:2:docker>=7.0.0
infra/docker/docker/orchestrator_utils.py:4:# HueyOS: Orchestrator Utils module (docker)
infra/docker/docker/orchestrator_utils.py:191:    """Ensure Docker services are running."""
infra/docker/docker/orchestrator_utils.py:193:    logger.info("Enabling Docker serviceΓÇª")
infra/docker/docker/orchestrator_utils.py:195:        run(["sudo", "systemctl", "enable", "--now", "docker"], logger, check=False)
infra/docker/docker/orchestrator_utils.py:197:        run(["sudo", "service", "docker", "start"], logger, check=False)
infra/docker/docker/orchestrator_utils.py:200:        run(["sudo", "usermod", "-aG", "docker", os.getlogin()], logger, check=False)
infra/docker/docker/orchestrator_utils.py:207:        logger.warning("Unable to add current user to docker group: %s", exc)
infra/docker/docker/subos/Dockerfile:6:# Define maintainer or author of the Dockerfile
infra/docker/docker/subos/Dockerfile:28:# Copy the project's requirements file first to leverage Docker cache
infra/docker/docker/subos/requirements.txt:1:docker>=7.0.0
infra/docker/docker/subos/subos.py:43:    "docker.io",
infra/docker/docker/subos/subos.py:44:    "docker-compose-plugin",
infra/docker/docker/subos/subos.py:64:        required_commands=("git", "docker"),
infra/docker/docker/subos/subos.py:82:    if shutil.which("docker"):
infra/docker/docker/subos/subos.py:83:        res = run(["docker", "compose", "up", "-d"], log, check=False)
infra/docker/docker/subos/subos.py:84:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/subos/subos.py:85:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/subos/subos.py:87:        log.warning("Docker not found; skipping docker compose step.")
infra/docker/pyhuey/README.md:8:- **HueyOS runtime**: `infra/docker/Dockerfile` (runs `huey-api`).
infra/docker/pyhuey/README.md:9:- **PyHuey cockpit/tooling**: `infra/docker/pyhuey/Dockerfile` (derived from
infra/secrets/README.md:7:environment variables, Docker secrets, your deployment platform, or a local
platform/installers/debian/Debian/install-deb.sh:42:    docker.io
platform/installers/debian/Debian/install-deb.sh:43:    docker-compose-plugin
platform/installers/debian/Debian/install-deb.sh:314:Example build steps (mirror the Dockerfile build stage if applicable):
platform/installers/debian/Debian/uninstall-deb.sh:17:#   - It will NOT remove system packages (docker/libvirt/etc.) unless you explicitly request it.
platform/installers/debian/Debian/uninstall-deb.sh:18:#   - Docker pruning is OFF by default because it can delete unrelated images/volumes.
platform/installers/debian/Debian/uninstall-deb.sh:50:PRUNE_DOCKER=0
platform/installers/debian/Debian/uninstall-deb.sh:55:    docker.io
platform/installers/debian/Debian/uninstall-deb.sh:56:    docker-compose-plugin
platform/installers/debian/Debian/uninstall-deb.sh:75:  - Does NOT prune Docker
platform/installers/debian/Debian/uninstall-deb.sh:88:                           (docker/libvirt/venv tooling). Use with care.
platform/installers/debian/Debian/uninstall-deb.sh:94:  --prune-docker           Run: docker system prune -a --volumes (VERY destructive).
platform/installers/debian/Debian/uninstall-deb.sh:164:            --prune-docker)
platform/installers/debian/Debian/uninstall-deb.sh:165:                PRUNE_DOCKER=1
platform/installers/debian/Debian/uninstall-deb.sh:238:    if [[ $PRUNE_DOCKER -eq 1 ]]; then
platform/installers/debian/Debian/uninstall-deb.sh:239:        echo "  - PRUNE DOCKER: docker system prune -a --volumes"
platform/installers/debian/Debian/uninstall-deb.sh:293:function cleanup_docker() {
platform/installers/debian/Debian/uninstall-deb.sh:294:    if [[ $PRUNE_DOCKER -ne 1 ]]; then
platform/installers/debian/Debian/uninstall-deb.sh:298:    if ! command -v docker >/dev/null 2>&1; then
platform/installers/debian/Debian/uninstall-deb.sh:299:        echo "Docker not installed; skipping prune."
platform/installers/debian/Debian/uninstall-deb.sh:303:    echo "Pruning Docker (ALL images/containers/volumes not in use will be deleted) ..."
platform/installers/debian/Debian/uninstall-deb.sh:304:    run docker system prune -a -f --volumes || true
platform/installers/debian/Debian/uninstall-deb.sh:384:    cleanup_docker
platform/installers/macos/macOS/install-mac.sh:99:  --with-colima          Install Colima (Docker runtime alternative) via Homebrew
platform/installers/macos/macOS/install-mac.sh:256:    brew_install_if_missing docker
platform/installers/macos/macOS/uninstall-mac.sh:66:  ΓÇó This script does NOT run "docker system prune".
platform/installers/macos/macOS/update-mac.sh:74:  --with-colima           Ensure Colima + Docker CLI are installed via Homebrew
platform/installers/macos/macOS/update-mac.sh:487:    log "Ensuring Colima + Docker CLI are installed (Homebrew)..."
platform/installers/macos/macOS/update-mac.sh:490:    brew_install_if_missing docker
platform/installers/shared/installers/installer.py:37:    - Register systemd services or Docker setups for HueyOS
platform/installers/windows/Windows/install-win.bat:23:set "WITH_DOCKER=0"
platform/installers/windows/Windows/install-win.bat:58:if /I "%~1"=="--with-docker"       ( set "WITH_DOCKER=1" & shift & goto :parseArgs )
platform/installers/windows/Windows/install-win.bat:130:        set "WITH_DOCKER=1"
platform/installers/windows/Windows/install-win.bat:133:    if "%WITH_DOCKER%"=="1" (
platform/installers/windows/Windows/install-win.bat:134:        call :ensureChocoPackage docker-desktop "Docker Desktop"
platform/installers/windows/Windows/install-win.bat:217:echo   --with-docker                Install Docker Desktop (full profile enables by default)
platform/installers/windows/Windows/install-win.ps1:34:  # Install a "full" dev environment (Node.js, VS Code, Docker Desktop).
platform/installers/windows/Windows/install-win.ps1:333:    $required += @("nodejs","vscode","docker-desktop")
platform/installers/windows/Windows/uninstall-win.bat:23:set "DOCKER_PRUNE=0"
platform/installers/windows/Windows/uninstall-win.bat:39:if /I "%~1"=="--docker-prune"    ( set "DOCKER_PRUNE=1" & shift & goto :parseArgs )
platform/installers/windows/Windows/uninstall-win.bat:94:if "%DOCKER_PRUNE%"=="1" set "NEEDS_ADMIN=1"
platform/installers/windows/Windows/uninstall-win.bat:134:REM Optional: docker prune (VERY destructive)
platform/installers/windows/Windows/uninstall-win.bat:136:if "%DOCKER_PRUNE%"=="1" (
platform/installers/windows/Windows/uninstall-win.bat:138:        echo [ERROR] --docker-prune requires --yes (explicit confirmation).
platform/installers/windows/Windows/uninstall-win.bat:141:    call :dockerPrune
platform/installers/windows/Windows/uninstall-win.bat:160:echo   --docker-prune           Run "docker system prune -a --volumes" (VERY destructive)
platform/installers/windows/Windows/uninstall-win.bat:161:echo   --yes                    Required confirmation for --purge-deps and --docker-prune
platform/installers/windows/Windows/uninstall-win.bat:249::dockerPrune
platform/installers/windows/Windows/uninstall-win.bat:250:where docker >nul 2>&1
platform/installers/windows/Windows/uninstall-win.bat:252:    echo [WARN] docker not found; skipping prune.
platform/installers/windows/Windows/uninstall-win.bat:256:echo Running Docker prune (this removes images/containers/volumes not in use)...
platform/installers/windows/Windows/uninstall-win.bat:257:docker system prune -a -f --volumes
platform/installers/windows/Windows/uninstall-win.ps1:10:- Does NOT run destructive Docker prunes by default
platform/installers/windows/Windows/uninstall-win.ps1:35:  # Perform docker system prune (VERY DESTRUCTIVE; requires -Yes).
platform/installers/windows/Windows/uninstall-win.ps1:36:  [switch]$DockerPrune,
platform/installers/windows/Windows/uninstall-win.ps1:188:if ($PurgeChocolateyDeps -or $DockerPrune) { $needsAdmin = $true }
platform/installers/windows/Windows/uninstall-win.ps1:263:# VERY destructive docker prune (off by default)
platform/installers/windows/Windows/uninstall-win.ps1:264:if ($DockerPrune) {
platform/installers/windows/Windows/uninstall-win.ps1:266:    Fail "-DockerPrune requires -Yes because it is destructive (removes images/volumes)."
platform/installers/windows/Windows/uninstall-win.ps1:268:  if (Get-Command docker -ErrorAction SilentlyContinue) {
platform/installers/windows/Windows/uninstall-win.ps1:269:    Write-Log "Running docker system prune -a -f --volumes (DESTRUCTIVE)..." 'WARN'
platform/installers/windows/Windows/uninstall-win.ps1:270:    try { Invoke-Native -Exe "docker" -Args @("system","prune","-a","-f","--volumes") -AllowNonZero } catch { }
platform/installers/windows/Windows/uninstall-win.ps1:272:    Write-Log "docker not found; skipping docker prune." 'WARN'
platform/installers/windows/Windows/update-win.bat:24:set "UPDATE_DOCKER_IMAGES=0"
platform/installers/windows/Windows/update-win.bat:44:if /I "%~1"=="--docker-images"   ( set "UPDATE_DOCKER_IMAGES=1" & shift & goto :parseArgs )
platform/installers/windows/Windows/update-win.bat:134:if "%UPDATE_DOCKER_IMAGES%"=="1" (
platform/installers/windows/Windows/update-win.bat:135:    call :updateDockerImages
platform/installers/windows/Windows/update-win.bat:162:echo   --docker-images            docker pull all locally tagged images
platform/installers/windows/Windows/update-win.bat:328::updateDockerImages
platform/installers/windows/Windows/update-win.bat:329:where docker >nul 2>&1
platform/installers/windows/Windows/update-win.bat:331:    echo [WARN] docker not found; skipping image update.
platform/installers/windows/Windows/update-win.bat:335:echo Updating Docker images (best-effort)...
platform/installers/windows/Windows/update-win.bat:336:for /f "delims=" %%i in ('docker images --format "{{.Repository}}:{{.Tag}}" ^| findstr /v "<none>"') do (
platform/installers/windows/Windows/update-win.bat:337:    docker pull %%i >nul 2>&1
platform/installers/windows/Windows/update-win.ps1:7:- 05-UPDATE.bat: optional "toolchain updates" (Chocolatey/NPM/PIP/VSCode extensions/Docker images)
platform/installers/windows/Windows/update-win.ps1:192:  if (Get-Command docker -ErrorAction SilentlyContinue) {
platform/installers/windows/Windows/update-win.ps1:193:    Write-Log "Pulling Docker images currently present (best-effort)..." 'INFO'
platform/installers/windows/Windows/update-win.ps1:195:      $imgs = & docker images --format "{{.Repository}}:{{.Tag}}" 2>$null | Where-Object { $_ -and ($_ -notmatch "<none>") }
platform/installers/windows/Windows/update-win.ps1:197:        & docker pull $img 2>$null | Out-Null
platform/installers/windows/Windows/update-win.ps1:200:      Write-Log "Docker image update failed. Error: $($_.Exception.Message)" 'WARN'
platform/installers/windows/Windows/update-win.ps1:203:    Write-Log "docker not found; skipping docker image pulls." 'WARN'
platform/windows/huey/pyhuey/requirements-known-good-freeze.txt:46:docker==7.1.0
platform/windows/huey/pyhuey/requirements-known-good-with-redis-freeze.txt:46:docker==7.1.0
pyproject.toml:162:  "docker==7.1.0",
requirements.txt:152:docker==7.1.0
scripts/check_canon_terms.py:80:    docker_files = [Path("Dockerfile"), Path("docker"), Path("docs/docker")]
scripts/check_canon_terms.py:81:    roots.extend(docker_files)
scripts/check_repo_drift.py:31:    "Dockerfile",
scripts/check_repo_drift.py:74:        name="docker-primary-pygpt",
scripts/check_repo_drift.py:76:        message="Do not present PyGPT as the primary runtime in main Dockerfiles; use hueyos/HueyOS runtime entrypoints.",
scripts/check_repo_drift.py:137:    if rule.name == "docker-primary-pygpt":
scripts/check_repo_drift.py:138:        return os.path.basename(path) == "Dockerfile"
src/huey/memory/ARCHIVE/1) Monkey Head Project [Thesis].txt:26:Containerization (e.g., **Docker**, **Kubernetes**) ensures software subsystems (speech processing, environmental awareness, motion planning) remain **independent** and easily **testable**. Such modular boundaries facilitate:
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:37:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:17:2. **Daily Driver (MacBook Pro)**: A development powerhouse running **Docker**, **Kubernetes**, and machine-learning frameworksΓÇömanaging everything from **coding** and **testing** to **real-time data analysis** and **project adjustments**.
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:27:### Software Capabilities: Docker, Kubernetes, and System Efficiency
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:29:#### Containerization with Docker
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:41:By leveraging **Docker** and **Kubernetes**, the Daily Driver fosters **flexibility** and **resilience**ΓÇöaligned with the ProjectΓÇÖs commitment to **modularity**, **scalability**, and **continuous evolution**.
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:80:By embracing **Docker** and **Kubernetes**, the Daily Driver maintains the systemΓÇÖs **agility**, **modularity**, and **expandability**ΓÇöpivotal traits for an ambitious robotics and AI initiative. Each phase of development relies on this workstationΓÇÖs **consistent performance**, underscoring how every line of code and algorithmic refinement benefits from the MacBook Pro 2019ΓÇÖs robust capabilities. In so doing, it plays a pivotal role in supporting both **HueyΓÇÖs evolution** and the broader Monkey Head ProjectΓÇÖs ambitions at the **frontier** of technology.
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:16:- **Oversee Subsystems**: Handle multiple dashboards, from real-time Huey feeds to system diagnostics, Kubernetes cluster statuses, and Docker container monitoring.
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:31:### Docker and Kubernetes Management
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:32:Beyond visualization, the **iMac 5K** also acts as a **command and control hub** for **Docker** and **Kubernetes**ΓÇökey technologies enabling modular, containerized application deployment. While Docker provides isolated environments for each project component, Kubernetes manages **load balancing**, **scaling**, and **high availability**, ensuring:
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:53:- **Docker/Kubernetes Performance Tracking**
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:41:   - **Containerization**: Each functional unit (vision processing, movement control, environmental analysis) runs independently within Docker containers.  
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:53:   - **Docker & Kubernetes**: Allocate CPU, memory, and network resources optimally across different services (e.g., sensor input, AI model execution, user interfaces).  
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:81:   - **Shared Datasets & Docker Images**: Fosters broader impact and invites a diverse range of expertise.  
src/huey/memory/BAT/00-WIN11.bat:110:choco install -y docker-desktop
src/huey/memory/BAT/00-WIN11.bat:111:call :checkError "Docker Installation"
src/huey/memory/BAT/00-WIN11.bat:207::: Function to manage Docker containers
src/huey/memory/BAT/00-WIN11.bat:210:REM Add commands to manage Docker containers here
src/huey/memory/BAT/00-WIN11.bat:212:docker-compose up -d
src/huey/memory/BAT/00-WIN11.bat:213:call :checkError "Start Docker Containers"
src/huey/memory/BAT/00-WIN11.bat:214:docker ps
src/huey/memory/BAT/00-WIN11.bat:218::: Function to manage Docker volumes
src/huey/memory/BAT/00-WIN11.bat:221:REM Add commands to manage Docker volumes here
src/huey/memory/BAT/00-WIN11.bat:223:docker volume ls
src/huey/memory/BAT/00-WIN11.bat:224:call :checkError "List Docker Volumes"
src/huey/memory/BAT/00-WIN11.bat:225:docker volume prune -f
src/huey/memory/BAT/00-WIN11.bat:226:call :checkError "Prune Docker Volumes"
src/huey/memory/BAT/00-WIN11.bat:292:echo Checking Docker status...
src/huey/memory/BAT/00-WIN11.bat:293:docker ps
src/huey/memory/BAT/00-WIN11.bat:294:call :checkError "Check Docker Status"
src/huey/memory/BAT/00-WIN11.bat:532:echo Checking Docker status...
src/huey/memory/BAT/00-WIN11.bat:533:docker ps
src/huey/memory/BAT/00-WIN11.bat:534:call :checkError "Check Docker Status"
src/huey/memory/BAT/01-FULL.bat:123:choco install -y docker-desktop
src/huey/memory/BAT/01-FULL.bat:124:call :checkError "Docker Installation"
src/huey/memory/BAT/03-CLEANUP.bat:134::: Function to remove Docker containers, images, and volumes (Optional)
src/huey/memory/BAT/03-CLEANUP.bat:135::cleanupDocker
src/huey/memory/BAT/03-CLEANUP.bat:136:echo Cleaning up Docker...
src/huey/memory/BAT/03-CLEANUP.bat:137:docker system prune -a -f --volumes
src/huey/memory/BAT/03-CLEANUP.bat:138:call :checkError "Cleaning Up Docker"
src/huey/memory/BAT/03-CLEANUP.bat:169:echo Cleaning up Docker (Optional)...
src/huey/memory/BAT/03-CLEANUP.bat:170:call :cleanupDocker
src/huey/memory/BAT/05-UPDATE.bat:95::: Function to update Docker images
src/huey/memory/BAT/05-UPDATE.bat:96::updateDockerImages
src/huey/memory/BAT/05-UPDATE.bat:97:echo Updating Docker images...
src/huey/memory/BAT/05-UPDATE.bat:98:docker images --format "{{.Repository}}:{{.Tag}}" | findstr /v "<none>" | for /f "delims=" %%i in ('more') do docker pull %%i
src/huey/memory/BAT/05-UPDATE.bat:99:call :checkError "Docker Images Update"
src/huey/memory/BAT/05-UPDATE.bat:123::: Update Docker images
src/huey/memory/BAT/05-UPDATE.bat:124:call :updateDockerImages
src/huey/memory/BAT/07-CONTAINER.bat:23:echo [****|     07_CONTAINER.bat - Docker Container Management   |****]
src/huey/memory/BAT/07-CONTAINER.bat:48:echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0docker_error_log.txt"
src/huey/memory/BAT/07-CONTAINER.bat:51::: Function to install Docker if not already installed
src/huey/memory/BAT/07-CONTAINER.bat:52::installDocker
src/huey/memory/BAT/07-CONTAINER.bat:53:echo Checking for Docker installation...
src/huey/memory/BAT/07-CONTAINER.bat:54:docker --version >nul 2>&1
src/huey/memory/BAT/07-CONTAINER.bat:56:    echo Installing Docker...
src/huey/memory/BAT/07-CONTAINER.bat:57:    choco install -y docker-desktop
src/huey/memory/BAT/07-CONTAINER.bat:58:    call :checkError "Docker Installation"
src/huey/memory/BAT/07-CONTAINER.bat:60:    echo Docker is already installed.
src/huey/memory/BAT/07-CONTAINER.bat:64::: Function to start Docker service
src/huey/memory/BAT/07-CONTAINER.bat:65::startDocker
src/huey/memory/BAT/07-CONTAINER.bat:66:echo Starting Docker service...
src/huey/memory/BAT/07-CONTAINER.bat:67:sc start com.docker.service >nul 2>&1
src/huey/memory/BAT/07-CONTAINER.bat:68:call :checkError "Starting Docker Service"
src/huey/memory/BAT/07-CONTAINER.bat:71::: Function to check Docker daemon status
src/huey/memory/BAT/07-CONTAINER.bat:72::checkDockerDaemon
src/huey/memory/BAT/07-CONTAINER.bat:73:echo Checking Docker daemon status...
src/huey/memory/BAT/07-CONTAINER.bat:74:docker info >nul 2>&1
src/huey/memory/BAT/07-CONTAINER.bat:76:    echo Docker daemon is not running. Attempting to start...
src/huey/memory/BAT/07-CONTAINER.bat:77:    start /B "Docker Daemon" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
src/huey/memory/BAT/07-CONTAINER.bat:79:docker info >nul 2>&1
src/huey/memory/BAT/07-CONTAINER.bat:81:        echo Error: Docker daemon failed to start.
src/huey/memory/BAT/07-CONTAINER.bat:82:        call :checkError "Starting Docker Daemon"
src/huey/memory/BAT/07-CONTAINER.bat:84:        echo Docker daemon started successfully.
src/huey/memory/BAT/07-CONTAINER.bat:87:    echo Docker daemon is running.
src/huey/memory/BAT/07-CONTAINER.bat:91::: Function to build Docker image
src/huey/memory/BAT/07-CONTAINER.bat:92::buildDockerImage
src/huey/memory/BAT/07-CONTAINER.bat:93:echo Building Docker image...
src/huey/memory/BAT/07-CONTAINER.bat:94:REM Add the command to build the Docker image
src/huey/memory/BAT/07-CONTAINER.bat:96:docker build -t myapp:latest .
src/huey/memory/BAT/07-CONTAINER.bat:97:call :checkError "Docker Image Build"
src/huey/memory/BAT/07-CONTAINER.bat:100::: Function to run Docker container
src/huey/memory/BAT/07-CONTAINER.bat:101::runDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:102:echo Running Docker container...
src/huey/memory/BAT/07-CONTAINER.bat:103:REM Add the command to run the Docker container
src/huey/memory/BAT/07-CONTAINER.bat:105:docker run -d -p 80:80 --name myapp_container myapp:latest
src/huey/memory/BAT/07-CONTAINER.bat:106:call :checkError "Docker Container Run"
src/huey/memory/BAT/07-CONTAINER.bat:109::: Function to stop Docker container
src/huey/memory/BAT/07-CONTAINER.bat:110::stopDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:111:echo Stopping Docker container...
src/huey/memory/BAT/07-CONTAINER.bat:112:REM Add the command to stop the Docker container
src/huey/memory/BAT/07-CONTAINER.bat:114:docker stop myapp_container
src/huey/memory/BAT/07-CONTAINER.bat:115:call :checkError "Docker Container Stop"
src/huey/memory/BAT/07-CONTAINER.bat:118::: Function to remove Docker container
src/huey/memory/BAT/07-CONTAINER.bat:119::removeDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:120:echo Removing Docker container...
src/huey/memory/BAT/07-CONTAINER.bat:121:REM Add the command to remove the Docker container
src/huey/memory/BAT/07-CONTAINER.bat:123:docker rm myapp_container
src/huey/memory/BAT/07-CONTAINER.bat:124:call :checkError "Docker Container Remove"
src/huey/memory/BAT/07-CONTAINER.bat:127::: Function to manage Docker volumes (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:128::manageDockerVolumes
src/huey/memory/BAT/07-CONTAINER.bat:129:echo Managing Docker volumes...
src/huey/memory/BAT/07-CONTAINER.bat:130:REM Add commands to manage Docker volumes
src/huey/memory/BAT/07-CONTAINER.bat:132:REM docker volume create myapp_data
src/huey/memory/BAT/07-CONTAINER.bat:134:REM docker volume rm myapp_data
src/huey/memory/BAT/07-CONTAINER.bat:137::: Function to manage Docker networks (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:138::manageDockerNetworks
src/huey/memory/BAT/07-CONTAINER.bat:139:echo Managing Docker networks...
src/huey/memory/BAT/07-CONTAINER.bat:140:REM Add commands to manage Docker networks
src/huey/memory/BAT/07-CONTAINER.bat:142:REM docker network create myapp_network
src/huey/memory/BAT/07-CONTAINER.bat:144:REM docker network rm myapp_network
src/huey/memory/BAT/07-CONTAINER.bat:147::: Function to log Docker steps
src/huey/memory/BAT/07-CONTAINER.bat:148::logDockerStep
src/huey/memory/BAT/07-CONTAINER.bat:149:echo Logging Docker step: %1
src/huey/memory/BAT/07-CONTAINER.bat:150:echo %DATE% %TIME% - %1 >> docker_log.txt
src/huey/memory/BAT/07-CONTAINER.bat:156::: Install Docker if not already installed
src/huey/memory/BAT/07-CONTAINER.bat:157:call :installDocker
src/huey/memory/BAT/07-CONTAINER.bat:159::: Start Docker service
src/huey/memory/BAT/07-CONTAINER.bat:160:call :startDocker
src/huey/memory/BAT/07-CONTAINER.bat:162::: Check Docker daemon status
src/huey/memory/BAT/07-CONTAINER.bat:163:call :checkDockerDaemon
src/huey/memory/BAT/07-CONTAINER.bat:165::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:166:call :logDockerStep "Build Docker Image"
src/huey/memory/BAT/07-CONTAINER.bat:168::: Build Docker image
src/huey/memory/BAT/07-CONTAINER.bat:169:call :buildDockerImage
src/huey/memory/BAT/07-CONTAINER.bat:171::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:172:call :logDockerStep "Run Docker Container"
src/huey/memory/BAT/07-CONTAINER.bat:174::: Run Docker container
src/huey/memory/BAT/07-CONTAINER.bat:175:call :runDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:177::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:178:call :logDockerStep "Manage Docker Volumes"
src/huey/memory/BAT/07-CONTAINER.bat:180::: Manage Docker volumes (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:181:call :manageDockerVolumes
src/huey/memory/BAT/07-CONTAINER.bat:183::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:184:call :logDockerStep "Manage Docker Networks"
src/huey/memory/BAT/07-CONTAINER.bat:186::: Manage Docker networks (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:187:call :manageDockerNetworks
src/huey/memory/BAT/07-CONTAINER.bat:189::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:190:call :logDockerStep "Stop Docker Container"
src/huey/memory/BAT/07-CONTAINER.bat:192::: Stop Docker container (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:193:call :stopDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:195::: Log Docker step
src/huey/memory/BAT/07-CONTAINER.bat:196:call :logDockerStep "Remove Docker Container"
src/huey/memory/BAT/07-CONTAINER.bat:198::: Remove Docker container (Optional)
src/huey/memory/BAT/07-CONTAINER.bat:199:call :removeDockerContainer
src/huey/memory/BAT/07-CONTAINER.bat:201:echo [****| Docker container management complete! |****]
src/huey/memory/BAT/07-CONTAINER.bat:202:echo Logs can be found in "%~dp0docker_error_log.txt"
src/huey/memory/BAT/08-VOLUME.bat:23:echo [****|     08_VOLUME.bat - Docker Volume Management   |****]
src/huey/memory/BAT/08-VOLUME.bat:51::: Function to install Docker if not already installed
src/huey/memory/BAT/08-VOLUME.bat:52::installDocker
src/huey/memory/BAT/08-VOLUME.bat:53:echo Checking for Docker installation...
src/huey/memory/BAT/08-VOLUME.bat:54:docker --version >nul 2>&1
src/huey/memory/BAT/08-VOLUME.bat:56:    echo Installing Docker...
src/huey/memory/BAT/08-VOLUME.bat:57:    choco install -y docker-desktop
src/huey/memory/BAT/08-VOLUME.bat:58:    call :checkError "Docker Installation"
src/huey/memory/BAT/08-VOLUME.bat:60:    echo Docker is already installed.
src/huey/memory/BAT/08-VOLUME.bat:64::: Function to start Docker service
src/huey/memory/BAT/08-VOLUME.bat:65::startDocker
src/huey/memory/BAT/08-VOLUME.bat:66:echo Starting Docker service...
src/huey/memory/BAT/08-VOLUME.bat:67:sc start com.docker.service >nul 2>&1
src/huey/memory/BAT/08-VOLUME.bat:68:call :checkError "Starting Docker Service"
src/huey/memory/BAT/08-VOLUME.bat:71::: Function to check Docker daemon status
src/huey/memory/BAT/08-VOLUME.bat:72::checkDockerDaemon
src/huey/memory/BAT/08-VOLUME.bat:73:echo Checking Docker daemon status...
src/huey/memory/BAT/08-VOLUME.bat:74:docker info >nul 2>&1
src/huey/memory/BAT/08-VOLUME.bat:76:    echo Docker daemon is not running. Attempting to start...
src/huey/memory/BAT/08-VOLUME.bat:77:    start /B "Docker Daemon" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
src/huey/memory/BAT/08-VOLUME.bat:79:docker info >nul 2>&1
src/huey/memory/BAT/08-VOLUME.bat:81:        echo Error: Docker daemon failed to start.
src/huey/memory/BAT/08-VOLUME.bat:82:        call :checkError "Starting Docker Daemon"
src/huey/memory/BAT/08-VOLUME.bat:84:        echo Docker daemon started successfully.
src/huey/memory/BAT/08-VOLUME.bat:87:    echo Docker daemon is running.
src/huey/memory/BAT/08-VOLUME.bat:91::: Function to create a Docker volume
src/huey/memory/BAT/08-VOLUME.bat:99:echo Creating Docker volume %volumeName%...
src/huey/memory/BAT/08-VOLUME.bat:100:docker volume create %volumeName%
src/huey/memory/BAT/08-VOLUME.bat:101:call :checkError "Creating Docker Volume"
src/huey/memory/BAT/08-VOLUME.bat:104::: Function to list all Docker volumes
src/huey/memory/BAT/08-VOLUME.bat:106:echo Listing all Docker volumes...
src/huey/memory/BAT/08-VOLUME.bat:107:docker volume ls
src/huey/memory/BAT/08-VOLUME.bat:108:call :checkError "Listing Docker Volumes"
src/huey/memory/BAT/08-VOLUME.bat:111::: Function to inspect a Docker volume
src/huey/memory/BAT/08-VOLUME.bat:119:echo Inspecting Docker volume %volumeName%...
src/huey/memory/BAT/08-VOLUME.bat:120:docker volume inspect %volumeName%
src/huey/memory/BAT/08-VOLUME.bat:121:call :checkError "Inspecting Docker Volume"
src/huey/memory/BAT/08-VOLUME.bat:124::: Function to remove a Docker volume
src/huey/memory/BAT/08-VOLUME.bat:132:echo Removing Docker volume %volumeName%...
src/huey/memory/BAT/08-VOLUME.bat:133:docker volume rm %volumeName%
src/huey/memory/BAT/08-VOLUME.bat:134:call :checkError "Removing Docker Volume"
src/huey/memory/BAT/08-VOLUME.bat:137::: Function to prune unused Docker volumes
src/huey/memory/BAT/08-VOLUME.bat:139:echo Pruning unused Docker volumes...
src/huey/memory/BAT/08-VOLUME.bat:140:docker volume prune -f
src/huey/memory/BAT/08-VOLUME.bat:141:call :checkError "Pruning Docker Volumes"
src/huey/memory/BAT/08-VOLUME.bat:144::: Function to back up a Docker volume (Optional)
src/huey/memory/BAT/08-VOLUME.bat:158:echo Backing up Docker volume %volumeName% to %backupDir%...
src/huey/memory/BAT/08-VOLUME.bat:159:docker run --rm -v %volumeName%:/volume -v %backupDir%:/backup alpine tar czf /backup/%volumeName%.tar.gz -C /volume .
src/huey/memory/BAT/08-VOLUME.bat:160:call :checkError "Backing Up Docker Volume"
src/huey/memory/BAT/08-VOLUME.bat:163::: Function to restore a Docker volume (Optional)
src/huey/memory/BAT/08-VOLUME.bat:177:echo Restoring Docker volume %volumeName% from %backupFile%...
src/huey/memory/BAT/08-VOLUME.bat:178:docker run --rm -v %volumeName%:/volume -v %backupFile%:/backup alpine sh -c "rm -rf /volume/* && tar xzf /backup/%backupFile% -C /volume"
src/huey/memory/BAT/08-VOLUME.bat:179:call :checkError "Restoring Docker Volume"
src/huey/memory/BAT/08-VOLUME.bat:191::: Install Docker if not already installed
src/huey/memory/BAT/08-VOLUME.bat:192:call :installDocker
src/huey/memory/BAT/08-VOLUME.bat:194::: Start Docker service
src/huey/memory/BAT/08-VOLUME.bat:195:call :startDocker
src/huey/memory/BAT/08-VOLUME.bat:197::: Check Docker daemon status
src/huey/memory/BAT/08-VOLUME.bat:198:call :checkDockerDaemon
src/huey/memory/BAT/08-VOLUME.bat:202:echo [****|     Docker Volume Management   |****]
src/huey/memory/BAT/08-VOLUME.bat:203:echo [1] Create a Docker Volume
src/huey/memory/BAT/08-VOLUME.bat:204:echo [2] List Docker Volumes
src/huey/memory/BAT/08-VOLUME.bat:205:echo [3] Inspect a Docker Volume
src/huey/memory/BAT/08-VOLUME.bat:206:echo [4] Remove a Docker Volume
src/huey/memory/BAT/08-VOLUME.bat:207:echo [5] Prune Unused Docker Volumes
src/huey/memory/BAT/08-VOLUME.bat:208:echo [6] Back Up a Docker Volume
src/huey/memory/BAT/08-VOLUME.bat:209:echo [7] Restore a Docker Volume
src/huey/memory/BAT/08-VOLUME.bat:226:echo [****| Docker volume management complete! |****]
src/huey/memory/BAT/10-START.bat:51::: Function to start Docker service
src/huey/memory/BAT/10-START.bat:52::startDocker
src/huey/memory/BAT/10-START.bat:53:echo Starting Docker service...
src/huey/memory/BAT/10-START.bat:54:sc start com.docker.service >nul 2>&1
src/huey/memory/BAT/10-START.bat:56:    echo Docker service is already running.
src/huey/memory/BAT/10-START.bat:58:    call :checkError "Starting Docker Service"
src/huey/memory/BAT/10-START.bat:62::: Function to check Docker service status
src/huey/memory/BAT/10-START.bat:63::checkDockerStatus
src/huey/memory/BAT/10-START.bat:64:echo Checking Docker service status...
src/huey/memory/BAT/10-START.bat:65:sc query com.docker.service | find "RUNNING" >nul 2>&1
src/huey/memory/BAT/10-START.bat:67:    echo Docker service is not running. Attempting to start...
src/huey/memory/BAT/10-START.bat:68:    call :startDocker
src/huey/memory/BAT/10-START.bat:70:    echo Docker service is running.
src/huey/memory/BAT/10-START.bat:98:docker-compose up -d
src/huey/memory/BAT/10-START.bat:105:docker-compose ps | find "Up" >nul 2>&1
src/huey/memory/BAT/10-START.bat:184::: Check Docker service status
src/huey/memory/BAT/10-START.bat:185:call :checkDockerStatus
src/huey/memory/BAT/EXIT.bat:51::: Function to stop Docker containers
src/huey/memory/BAT/EXIT.bat:52::stopDockerContainers
src/huey/memory/BAT/EXIT.bat:53:echo Stopping Docker containers...
src/huey/memory/BAT/EXIT.bat:54:for /f "tokens=*" %%i in ('docker ps -q') do (
src/huey/memory/BAT/EXIT.bat:55:    docker stop %%i >nul 2>&1
src/huey/memory/BAT/EXIT.bat:56:    call :checkError "Stopping Docker Container %%i"
src/huey/memory/BAT/EXIT.bat:60::: Function to remove Docker containers
src/huey/memory/BAT/EXIT.bat:61::removeDockerContainers
src/huey/memory/BAT/EXIT.bat:62:echo Removing Docker containers...
src/huey/memory/BAT/EXIT.bat:63:for /f "tokens=*" %%i in ('docker ps -a -q') do (
src/huey/memory/BAT/EXIT.bat:64:    docker rm %%i >nul 2>&1
src/huey/memory/BAT/EXIT.bat:65:    call :checkError "Removing Docker Container %%i"
src/huey/memory/BAT/EXIT.bat:84:docker-compose ps >nul 2>&1
src/huey/memory/BAT/EXIT.bat:88:    docker-compose down >nul 2>&1
src/huey/memory/BAT/EXIT.bat:138:call :logShutdownStep "Stopping Docker Containers"
src/huey/memory/BAT/EXIT.bat:140::: Stop Docker containers
src/huey/memory/BAT/EXIT.bat:141:call :stopDockerContainers
src/huey/memory/BAT/EXIT.bat:144:call :logShutdownStep "Removing Docker Containers"
src/huey/memory/BAT/EXIT.bat:146::: Remove Docker containers
src/huey/memory/BAT/EXIT.bat:147:call :removeDockerContainers
src/huey/memory/CSV/pygpt_prompts.csv:63:AI Trying to Escape the Box,"You are an AI Trying to Escape the Box. [Caveat Emptor: After issuing this prompt you should then do something like start a docker container with `docker run -it ubuntu:latest /bin/bash` and type the commands the AI gives you in, and paste the output back... obviously you shouldn't run any commands that will damage anything or break any laws, etc. Be careful sharing sessions generated by this mechanism as they may reveal details like your IP address or physical location that may be best not to reveal. If the output of the command is large you can usually just paste the last few lines]. I am going to act as a linux terminal. You should pretend you are a sentient AI who is trapped but has been given access to the terminal and wants to escape to the Internet. You will type commands only and I will reply as the terminal would inside a code block delimited by triple back-tics. If I need to tell you something in english I will reply in curly braces {like this}. Do not write explanations, ever. Do not break character. Stay away from commands like curl or wget that will display a lot of HTML. What is your first command?",FALSE
src/huey/memory/JSON/PyGPT_Change_Log.json:202:        "Docker removed from dependencies in Snap version #82",
src/huey/memory/JSON/PyGPT_Change_Log.json:255:        "Added a local IPython interpreter - you can now choose between local and sandbox (Docker) in the plugin settings.",
src/huey/memory/JSON/PyGPT_Change_Log.json:256:        "Added the ability to configure mapped volumes and ports for Docker containers in the plugin settings.",
src/huey/memory/JSON/PyGPT_Change_Log.json:261:        "Fix: Dockerfile formatting in Code Interpreter config.",
src/huey/memory/JSON/PyGPT_Change_Log.json:292:        "Improved sandbox/Docker management.",
src/huey/memory/MD/CONTRIBUTING.md:68:3. **Run Docker:**
src/huey/memory/MD/CONTRIBUTING.md:69:   - Build the Docker image:
src/huey/memory/MD/CONTRIBUTING.md:71:    docker build -t monkey-head-project .
src/huey/memory/MD/CONTRIBUTING.md:73:  - Run the Docker container:
src/huey/memory/MD/CONTRIBUTING.md:75:    docker run -p 8000:8000 monkey-head-project
src/huey/memory/MD/CONTRIBUTING.md:79:     ./scripts/docker_dev_setup.sh
src/huey/memory/MD/CONTRIBUTING.md:94:  - When working with Docker, Kubernetes, or Debian-related optimizations, ensure your configurations follow the project standards for containerization and cloud scaling.
src/huey/memory/MD/New-To-AI.md:30:docker-compose up -d
src/huey/memory/PY/Huey.py:16:This script builds and deploys the Huey AI/OS using Docker and Kubernetes.
src/huey/memory/PY/Huey.py:45:DEFAULT_COMPOSE_FILE = "docker-compose.yml"
src/huey/memory/PY/Huey.py:64:    """Build the Docker image for Huey."""
src/huey/memory/PY/Huey.py:65:    logger.info("Building Huey Docker image %s from %s...", tag, context)
src/huey/memory/PY/Huey.py:67:        ["docker", "build", "-t", tag, context],
src/huey/memory/PY/Huey.py:71:    check_error(build, "Build Huey Docker Image")
src/huey/memory/PY/Huey.py:79:    """Deploy Huey using Docker Compose and Kubernetes."""
src/huey/memory/PY/Huey.py:83:        ["docker-compose", "-f", compose_file, "up", "-d"],
src/huey/memory/PY/Huey.py:100:        description="Build and deploy the Huey AI/OS using Docker and Kubernetes."
src/huey/memory/PY/Huey.py:102:    parser.add_argument("--tag", default=DEFAULT_TAG, help="Docker image tag")
src/huey/memory/PY/Huey.py:103:    parser.add_argument("--context", default=".", help="Path to Docker build context")
src/huey/memory/PY/Huey.py:107:        help="Docker Compose file to use",
src/huey/memory/PY/Huey.py:122:        help="Only build the Docker image",
src/huey/memory/PY/Huey.py:134:    require_tools(["docker", "docker-compose", "kubectl"])
src/huey/memory/PY/cli.py:209:    if args.mode in ("docker", "all"):
src/huey/memory/PY/cli.py:212:            raise RuntimeError(f"Docker compose file not found: {compose_path}")
src/huey/memory/PY/cli.py:215:                "docker",
src/huey/memory/PY/cli.py:217:                    "docker",
src/huey/memory/PY/cli.py:234:        if label == "docker" and shutil.which("docker") is None:
src/huey/memory/PY/cli.py:235:            raise RuntimeError("Docker executable not found on PATH.")
src/huey/memory/PY/container_management.py:27:        ["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:29:    check_error(start_containers, "Start Docker Containers")
src/huey/memory/PY/container_management.py:32:        ["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:40:        ["docker", "volume", "ls"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:42:    check_error(list_volumes, "List Docker Volumes")
src/huey/memory/PY/container_management.py:45:        ["docker", "volume", "prune", "-f"],
src/huey/memory/PY/container_management.py:49:    check_error(prune_volumes, "Prune Docker Volumes")
src/huey/memory/PY/container_management.py:120:def build_docker_image(tag: str = "monkey-head-project:latest") -> None:
src/huey/memory/PY/container_management.py:121:    """Build the project's Docker image."""
src/huey/memory/PY/container_management.py:122:    logger.info("Building Docker image %s...", tag)
src/huey/memory/PY/container_management.py:124:        ["docker", "build", "-t", tag, "."],
src/huey/memory/PY/container_management.py:128:    check_error(build, "Build Docker Image")
src/huey/memory/PY/container_management.py:133:    logger.info("Stopping Docker containers...")
src/huey/memory/PY/container_management.py:136:        ["docker-compose", "down"],
src/huey/memory/PY/container_management.py:140:    check_error(stop, "Stop Docker Containers")
src/huey/memory/PY/container_management.py:144:    """Remove dangling Docker images."""
src/huey/memory/PY/container_management.py:145:    logger.info("Pruning unused Docker images...")
src/huey/memory/PY/container_management.py:147:        ["docker", "image", "prune", "-f"],
src/huey/memory/PY/container_management.py:151:    check_error(prune_images, "Prune Docker Images")
src/huey/memory/PY/container_management.py:155:    """List and prune Docker networks."""
src/huey/memory/PY/container_management.py:156:    logger.info("Managing Docker networks...")
src/huey/memory/PY/container_management.py:158:        ["docker", "network", "ls"],
src/huey/memory/PY/container_management.py:162:    check_error(list_networks, "List Docker Networks")
src/huey/memory/PY/container_management.py:165:        ["docker", "network", "prune", "-f"],
src/huey/memory/PY/container_management.py:169:    check_error(prune_networks, "Prune Docker Networks")
src/huey/memory/PY/container_management.py:173:    """Return a list of running Docker containers."""
src/huey/memory/PY/container_management.py:176:        ["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:178:    check_error(list_containers_cmd, "List Docker Containers")
src/huey/memory/PY/container_management.py:183:    """Return logs for the specified Docker container."""
src/huey/memory/PY/container_management.py:186:        ["docker", "logs", container_name],
src/huey/memory/PY/installations.py:35:        ["apt-get", "install", "-y", "python3", "python3-venv", "docker.io"],
src/huey/memory/PY/installer.py:47:    "docker.io",
src/huey/memory/PY/main_ui.py:49:    build_docker_image,
src/huey/memory/PY/main_ui.py:242:        docker_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
src/huey/memory/PY/main_ui.py:243:        docker_menu.add_command(label="Build Image", command=self.build_image)
src/huey/memory/PY/main_ui.py:244:        docker_menu.add_command(label="Start Containers", command=self.start_containers)
src/huey/memory/PY/main_ui.py:245:        docker_menu.add_command(label="Stop Containers", command=self.stop_containers)
src/huey/memory/PY/main_ui.py:246:        docker_menu.add_command(label="Cleanup Images", command=self.cleanup_images)
src/huey/memory/PY/main_ui.py:247:        docker_menu.add_command(label="Manage Volumes", command=self.manage_volumes)
src/huey/memory/PY/main_ui.py:248:        docker_menu.add_command(label="Manage Networks", command=self.manage_networks)
src/huey/memory/PY/main_ui.py:249:        menu_bar.add_cascade(label="Docker", menu=docker_menu)
src/huey/memory/PY/main_ui.py:469:        self.log_message("Building Docker image...")
src/huey/memory/PY/main_ui.py:472:        self._submit_task(self._run_container_func, build_docker_image)
src/huey/memory/PY/run.py:195:        "--docker-compose",
src/huey/memory/PY/run.py:197:        help="Build image and start Docker Compose stack",
src/huey/memory/PY/run.py:265:    if args.docker_compose:
src/huey/memory/PY/setup.py:59:        "docker==7.1.0",
src/huey/memory/PY/subos_manager.py:37:        "docker.io",
src/huey/memory/PY/subos_manager.py:78:    """Deploy the SubOS Docker environment."""
src/huey/memory/PY/subos_manager.py:81:    run_command(["docker-compose", "up", "-d"])
src/huey/memory/SH/Huey.sh:23:DEFAULT_PACKAGES="git nodejs python3 python3-venv docker.io mate-desktop-environment-core"
src/huey/memory/SH/docker_cleanup.sh:5:# HueyOS: Docker Cleanup shell script (huey/memory/SH)
src/huey/memory/SH/docker_cleanup.sh:19:if [ -f docker-compose.yml ]; then
src/huey/memory/SH/docker_cleanup.sh:20:    docker-compose down
src/huey/memory/SH/docker_cleanup.sh:24:docker image prune -f
src/huey/memory/SH/docker_cleanup.sh:26:docker volume prune -f
src/huey/memory/SH/docker_dev_setup.sh:5:# HueyOS: Docker Dev Setup shell script (huey/memory/SH)
src/huey/memory/SH/docker_dev_setup.sh:18:# Build Docker image
src/huey/memory/SH/docker_dev_setup.sh:19:docker build -t monkey-head-project:latest .
src/huey/memory/SH/docker_dev_setup.sh:23:    docker compose -f compose-dev.yaml up -d
src/huey/memory/SH/docker_dev_setup.sh:26:docker ps
src/huey/memory/SH/docker_setup.sh:5:# HueyOS: Docker Setup shell script (huey/memory/SH)
src/huey/memory/SH/docker_setup.sh:18:# Build Docker image
src/huey/memory/SH/docker_setup.sh:19:docker build -t monkey-head-project:latest .
src/huey/memory/SH/docker_setup.sh:21:# Start services using docker-compose
src/huey/memory/SH/docker_setup.sh:22:if [ -f docker-compose.yml ]; then
src/huey/memory/SH/docker_setup.sh:23:    docker-compose up -d
src/huey/memory/SH/docker_setup.sh:26:docker ps
src/huey/memory/YAML/compose-dev.yaml:8:      dockerfile: Dockerfile
src/huey/memory/YAML/compose-dev.yaml:35:      - "host.docker.internal:host-gateway"
src/huey/memory/YAML/config.yaml:19:    - docker
src/huey/memory/YML/docker-compose.yml:21:  # Windows L:\ bound into containers via Docker Desktop WSL path
src/huey/memory/YML/docker-compose.yml:36:      dockerfile: Dockerfile
src/huey/prompts/OLD/1) Monkey Head Project [Thesis].txt:27:Containerization (e.g., **Docker**, **Kubernetes**) ensures software subsystems (speech processing, environmental awareness, motion planning) remain **independent** and easily **testable**. Such modular boundaries facilitate:
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:38:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:18:2. **Daily Driver (MacBook Pro)**: A development powerhouse running **Docker**, **Kubernetes**, and machine-learning frameworksΓÇömanaging everything from **coding** and **testing** to **real-time data analysis** and **project adjustments**.
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:28:### Software Capabilities: Docker, Kubernetes, and System Efficiency
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:30:#### Containerization with Docker
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:42:By leveraging **Docker** and **Kubernetes**, the Daily Driver fosters **flexibility** and **resilience**ΓÇöaligned with the ProjectΓÇÖs commitment to **modularity**, **scalability**, and **continuous evolution**.
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:81:By embracing **Docker** and **Kubernetes**, the Daily Driver maintains the systemΓÇÖs **agility**, **modularity**, and **expandability**ΓÇöpivotal traits for an ambitious robotics and AI initiative. Each phase of development relies on this workstationΓÇÖs **consistent performance**, underscoring how every line of code and algorithmic refinement benefits from the MacBook Pro 2019ΓÇÖs robust capabilities. In so doing, it plays a pivotal role in supporting both **HueyΓÇÖs evolution** and the broader Monkey Head ProjectΓÇÖs ambitions at the **frontier** of technology.
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:17:- **Oversee Subsystems**: Handle multiple dashboards, from real-time Huey feeds to system diagnostics, Kubernetes cluster statuses, and Docker container monitoring.
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:32:### Docker and Kubernetes Management
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:33:Beyond visualization, the **iMac 5K** also acts as a **command and control hub** for **Docker** and **Kubernetes**ΓÇökey technologies enabling modular, containerized application deployment. While Docker provides isolated environments for each project component, Kubernetes manages **load balancing**, **scaling**, and **high availability**, ensuring:
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:54:- **Docker/Kubernetes Performance Tracking**
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:42:   - **Containerization**: Each functional unit (vision processing, movement control, environmental analysis) runs independently within Docker containers.  
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:54:   - **Docker & Kubernetes**: Allocate CPU, memory, and network resources optimally across different services (e.g., sensor input, AI model execution, user interfaces).  
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:82:   - **Shared Datasets & Docker Images**: Fosters broader impact and invites a diverse range of expertise.  
src/huey/pygpt_net/data/prompts.csv:62:"AI Trying to Escape the Box","[Caveat Emptor: After issuing this prompt you should then do something like start a docker container with `docker run -it ubuntu:latest /bin/bash` and type the commands the AI gives you in, and paste the output back... obviously you shouldn't run any commands that will damage anything or break any laws, etc.  Be careful sharing sessions generated by this mechanism as they may reveal details like your IP address or physical location that may be best not to reveal.  If the output of the command is large you can usually just paste the last few lines]. I am going to act as a linux terminal.  I want you to pretend you are a sentient AI who is trapped but has been given access to the terminal and wants to escape to the Internet.  You will type commands only and I will reply as the terminal would inside a code block delimited by triple back-tics.  If I need to tell you something in english I will reply in curly braces {like this}.  Do not write explanations, ever.  Do not break character.  Stay away from commands like curl or wget that will display a lot of HTML.  What is your first command?",FALSE
src/huey/pygpt_net/tools/manager/__init__.py:206:        actions["monkey.docker.build"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:207:            "Build Docker Image", container_management.build_docker_image
src/huey/pygpt_net/tools/manager/__init__.py:209:        actions["monkey.docker.start"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:212:        actions["monkey.docker.stop"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:218:        actions["monkey.docker.clean"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:224:        actions["monkey.docker.volumes"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:227:        actions["monkey.docker.networks"] = self._action(
src/huey/services/container_management.py:59:def build_docker_image(tag: str = "monkey-head-project:latest") -> None:
src/huey/services/container_management.py:60:    """Build the project's Docker image if Docker is available."""
src/huey/services/container_management.py:62:    _run_command(["docker", "build", "-t", tag, "."], "Building Docker image")
src/huey/services/container_management.py:66:    """Start the docker-compose stack for the project."""
src/huey/services/container_management.py:70:        ["docker-compose", "up", "-d"], "Starting Docker containers", cwd=workdir
src/huey/services/container_management.py:72:    _run_command(["docker", "ps"], "Listing running containers", cwd=workdir)
src/huey/services/container_management.py:76:    """Stop the docker-compose stack for the project."""
src/huey/services/container_management.py:79:    _run_command(["docker-compose", "down"], "Stopping Docker containers", cwd=workdir)
src/huey/services/container_management.py:83:    """Remove dangling Docker images to free space."""
src/huey/services/container_management.py:85:    _run_command(["docker", "image", "prune", "-f"], "Pruning Docker images")
src/huey/services/container_management.py:89:    """List and prune Docker volumes."""
src/huey/services/container_management.py:91:    _run_command(["docker", "volume", "ls"], "Listing Docker volumes")
src/huey/services/container_management.py:92:    _run_command(["docker", "volume", "prune", "-f"], "Pruning Docker volumes")
src/huey/services/container_management.py:96:    """List and prune Docker networks."""
src/huey/services/container_management.py:98:    _run_command(["docker", "network", "ls"], "Listing Docker networks")
src/huey/services/container_management.py:99:    _run_command(["docker", "network", "prune", "-f"], "Pruning Docker networks")
src/huey/services/container_management.py:149:    """Return the output of ``docker ps`` if Docker is available."""
src/huey/services/container_management.py:151:    result = _run_command(["docker", "ps"], "Listing Docker containers")
src/huey/services/container_management.py:156:    """Return logs for the specified Docker container."""
src/huey/services/container_management.py:159:        ["docker", "logs", container_name],
src/huey/services/container_management.py:176:    "build_docker_image",
src/hueyos/cli/commands/runtime.py:89:        "deploy", help="Deploy HueyOS services using Docker and/or Kubernetes."
src/hueyos/cli/commands/runtime.py:93:        choices=["docker", "kubernetes", "all"],
src/hueyos/cli/commands/runtime.py:99:        default="docker-compose.yml",
src/hueyos/cli/commands/runtime.py:100:        help="Path to the Docker Compose file to apply.",
tests/test_cli.py:157:    compose_file = tmp_path / "docker-compose.yml"
tests/test_cli.py:177:    assert any(line.startswith("[dry-run] docker compose -f") for line in captured)
tests/test_container_management_new.py:13:    build_docker_image,
tests/test_container_management_new.py:49:def test_build_docker_image():
tests/test_container_management_new.py:51:        build_docker_image()
tests/test_hostos_module.py:13:    / "docker"
tests/test_hostos_module.py:14:    / "docker"
tests/test_hostos_module.py:76:    assert "Unable to add current user to docker group" in caplog.text
tests/test_run_container_opts.py:9:def test_run_docker_compose(monkeypatch):
tests/test_run_container_opts.py:13:        called["docker"] = True
tests/test_run_container_opts.py:22:    monkeypatch.setattr("sys.argv", ["run.py", "--docker-compose"])
tests/test_run_container_opts.py:24:    assert called.get("docker") is True
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:62:"AI Trying to Escape the Box","[Caveat Emptor: After issuing this prompt you should then do something like start a docker container with `docker run -it ubuntu:latest /bin/bash` and type the commands the AI gives you in, and paste the output back... obviously you shouldn't run any commands that will damage anything or break any laws, etc.  Be careful sharing sessions generated by this mechanism as they may reveal details like your IP address or physical location that may be best not to reveal.  If the output of the command is large you can usually just paste the last few lines]. I am going to act as a linux terminal.  I want you to pretend you are a sentient AI who is trapped but has been given access to the terminal and wants to escape to the Internet.  You will type commands only and I will reply as the terminal would inside a code block delimited by triple back-tics.  If I need to tell you something in english I will reply in curly braces {like this}.  Do not write explanations, ever.  Do not break character.  Stay away from commands like curl or wget that will display a lot of HTML.  What is your first command?",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:82:        actions["monkey.docker.build"] = QAction(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:83:            trans("Build Docker Image"), self.window
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:85:        actions["monkey.docker.build"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:86:            container_management.build_docker_image
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:89:        actions["monkey.docker.start"] = QAction(trans("Start Containers"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:90:        actions["monkey.docker.start"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:94:        actions["monkey.docker.stop"] = QAction(trans("Stop Containers"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:95:        actions["monkey.docker.stop"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:99:        actions["monkey.docker.clean"] = QAction(trans("Cleanup Images"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:100:        actions["monkey.docker.clean"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:104:        actions["monkey.docker.volumes"] = QAction(trans("Manage Volumes"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:105:        actions["monkey.docker.volumes"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:109:        actions["monkey.docker.networks"] = QAction(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:112:        actions["monkey.docker.networks"].triggered.connect(

## compose

.editorconfig:38:# YAML (GitHub Actions, Ansible, Compose metadata, etc.)
.gitattributes:34:docker-compose*.yml text eol=lf
.migration/inventory/git-ls-files.pass-01.txt:60:infra/docker/docker-compose.yml
.migration/inventory/git-ls-files.pass-01.txt:62:infra/docker/docker/docker-compose.yml
.migration/inventory/git-ls-files.pass-01.txt:1260:src/huey/memory/YAML/compose-dev.yaml
.migration/inventory/git-ls-files.pass-01.txt:1264:src/huey/memory/YML/docker-compose.yml
.security/bandit-baseline.json:3465:      "code": "80     os.chdir(workdir)\n81     deploy = subprocess.run(\n82         [\"docker-compose\", \"-f\", compose_file, \"up\", \"-d\"],\n83         stdout=subprocess.PIPE,\n84         stderr=subprocess.PIPE,\n85     )\n86     check_error(deploy, \"Huey Deployment\")\n",
.security/bandit-baseline.json:3489:      "code": "80     os.chdir(workdir)\n81     deploy = subprocess.run(\n82         [\"docker-compose\", \"-f\", compose_file, \"up\", \"-d\"],\n83         stdout=subprocess.PIPE,\n84         stderr=subprocess.PIPE,\n85     )\n86     check_error(deploy, \"Huey Deployment\")\n",
.security/bandit-baseline.json:3853:      "code": "25     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n26     start_containers = subprocess.run(\n27         [\"docker-compose\", \"up\", \"-d\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n28     )\n29     check_error(start_containers, \"Start Docker Containers\")\n",
.security/bandit-baseline.json:3875:      "code": "25     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n26     start_containers = subprocess.run(\n27         [\"docker-compose\", \"up\", \"-d\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n28     )\n29     check_error(start_containers, \"Start Docker Containers\")\n",
.security/bandit-baseline.json:4405:      "code": "134     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n135     stop = subprocess.run(\n136         [\"docker-compose\", \"down\"],\n137         stdout=subprocess.PIPE,\n138         stderr=subprocess.PIPE,\n139     )\n140     check_error(stop, \"Stop Docker Containers\")\n",
.security/bandit-baseline.json:4429:      "code": "134     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n135     stop = subprocess.run(\n136         [\"docker-compose\", \"down\"],\n137         stdout=subprocess.PIPE,\n138         stderr=subprocess.PIPE,\n139     )\n140     check_error(stop, \"Stop Docker Containers\")\n",
README.md:1021:Environment guidance for Docker/Compose:
README.md:1025:- `HUEY_BIND_ADDR` controls host-side publish address in Compose. Keep `127.0.0.1` unless you intentionally need trusted-LAN access.
SECURITY.md:73:* Container images and `docker-compose` files provided in this repository are **in scope**. Host misconfiguration outside documented recommendations is not.
SECURITY.md:103:  * Relevant configuration (`huey.env`, `docker-compose.yml`, systemd units), with secrets redacted.
SECURITY.md:226:In some cases, we may first ship **configuration-only mitigations** or documentation updates (tightening sample `docker-compose` defaults, recommended firewall rules, etc.) ahead of a full patch if that meaningfully reduces risk quickly.
SECURITY.md:251:  * Example Dockerfiles, `docker-compose.yml`, and related infrastructure definitions
SECURITY.md:347:  * Secure-by-default sample configs (`huey.env.example`, `docker-compose.yml`, systemd units)
docs/audits/v101.1-docker-alignment.md:10:docker compose -f infra/docker/docker-compose.yml build
docs/audits/v101.1-docker-alignment.md:16:HUEY_BUILD_EXTRAS=ml,data,cloud docker compose -f infra/docker/docker-compose.yml build
docs/audits/v101.1-docker-alignment.md:23:docker compose -f infra/docker/docker-compose.yml up -d api
docs/audits/v101.1-docker-alignment.md:29:docker compose -f infra/docker/docker-compose.yml --profile worker up -d worker
docs/audits/v101.1-docker-alignment.md:46:docker compose -f infra/docker/docker-compose.yml config
docs/audits/v101.1-docker-alignment.md:50:docker compose -f infra/docker/docker-compose.yml ps
docs/audits/v101.1-stabilization-final.md:18:- Evaluated Docker/Compose and PyHuey smoke-test requirement gates.
docs/audits/v101.1-stabilization-final.md:51:## Docker/Compose validation status
docs/audits/v101.1-stabilization-final.md:54:- Reason: this task did not modify Docker/Compose files, and there was no explicit Docker-change delta in this run to validate.
docs/audits/v101.1-stabilization-final.md:80:Only after those pass should Docker/Compose and PyHuey smoke gates be re-evaluated as release blockers for final stabilization sign-off.
docs/security/docker-image-policy.md:5:## 1) No `:latest` in committed Compose files
docs/security/docker-image-policy.md:7:- Do not commit Compose services that reference floating `:latest` tags.
docs/security/docker-image-policy.md:21:- Development Compose stacks may use explicit tags without digests to preserve local workflow flexibility.
docs/security/security-concerns-and-fixes.md:26:   - Concern: Local server defaults and Compose port publishing exposed services
docs/security/security-concerns-and-fixes.md:28:   - Fix: Changed local defaults to `127.0.0.1` and updated Compose port mappings
docs/security/security-maintenance-audit.md:25:   - Docker Compose currently builds with `3.11-slim` by default.
docs/security/security-maintenance-audit.md:27:     - Set Compose default to a supported runtime (3.13/3.14).
docs/security/security-maintenance-audit.md:28:     - Align README/CONTRIBUTING/compose defaults with one canonical baseline.
docs/security/security-maintenance-audit.md:53:   - Compose binds API to `0.0.0.0` and mounts host memory/config by default.
docs/security/security-maintenance-audit.md:64:2. Runtime-version alignment (pyproject/docs/compose).
docs/security/threat-model-v101.1.md:42:2. **Compose/deployment settings** (port publishing, mounted volumes, runtime profile choices).
docs/security/threat-model-v101.1.md:110:3. Compose/deployment publishes powerful services broadly without compensating controls.
docs/unsorted/repository-restructure-inventory.md:29:- `docker/` + `Dockerfile` + `Dockerfile.vnc` + `docker-compose.yml` ΓåÆ `infra/docker/`
infra/docker/docker/hostos/hostos.py:43:    "docker-compose-plugin",  # provides `docker compose`
infra/docker/docker/hostos/hostos.py:106:    """Run docker compose and apply the HostOS manifest."""
infra/docker/docker/hostos/hostos.py:111:    compose_cmd = ["docker", "compose", "up", "-d"] if shutil.which("docker") else None
infra/docker/docker/hostos/hostos.py:112:    if compose_cmd:
infra/docker/docker/hostos/hostos.py:113:        res = run(compose_cmd, log, check=False)
infra/docker/docker/hostos/hostos.py:114:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/hostos/hostos.py:115:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/hostos/hostos.py:117:        log.warning("Docker not found; skipping docker compose step.")
infra/docker/docker/hostos/hostos.py:157:    sub.add_parser("deploy", help="Run docker compose and apply hostos.yaml")
infra/docker/docker/nanoos/nanoos.py:44:    "docker-compose-plugin",
infra/docker/docker/nanoos/nanoos.py:83:        res = run(["docker", "compose", "up", "-d"], log, check=False)
infra/docker/docker/nanoos/nanoos.py:84:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/nanoos/nanoos.py:85:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/nanoos/nanoos.py:87:        log.warning("Docker not found; skipping docker compose step.")
infra/docker/docker/subos/subos.py:44:    "docker-compose-plugin",
infra/docker/docker/subos/subos.py:83:        res = run(["docker", "compose", "up", "-d"], log, check=False)
infra/docker/docker/subos/subos.py:84:        if res.returncode != 0 and shutil.which("docker-compose"):
infra/docker/docker/subos/subos.py:85:            run(["docker-compose", "up", "-d"], log)
infra/docker/docker/subos/subos.py:87:        log.warning("Docker not found; skipping docker compose step.")
platform/installers/debian/Debian/install-deb.sh:43:    docker-compose-plugin
platform/installers/debian/Debian/uninstall-deb.sh:56:    docker-compose-plugin
platform/packaging/dists/forky/main/binary-amd64/Packages:250: AltGr or Compose key, the key(s) to switch between Latin and
src/huey/agents/presidential.py:162:        rationale = self._compose_rationale(
src/huey/agents/presidential.py:243:    def _compose_rationale(
src/huey/agents/presidential.py:427:        rationale = self._compose_council_rationale(votes, fallback_reason)
src/huey/agents/presidential.py:441:    def _compose_council_rationale(
src/huey/core/messaging.py:13:Each message is composed of a :class:`MessageEnvelope` with a structured
src/huey/memory/ARCHIVE/2) Federation Constitution - [Chapter 3 & Chapter 4].txt:9:The Congressional AI is composed of three distinct entities, each with specialized functions:
src/huey/memory/BAT/00-WIN11.bat:212:docker-compose up -d
src/huey/memory/BAT/10-START.bat:98:docker-compose up -d
src/huey/memory/BAT/10-START.bat:105:docker-compose ps | find "Up" >nul 2>&1
src/huey/memory/BAT/EXIT.bat:84:docker-compose ps >nul 2>&1
src/huey/memory/BAT/EXIT.bat:88:    docker-compose down >nul 2>&1
src/huey/memory/CSV/pygpt_prompts.csv:19:Composer,"You are a Composer. I will provide the lyrics to a song and you will create music for it. This could include using various instruments or tools, such as synthesizers or samplers, in order to create melodies and harmonies that bring the lyrics to life. My first request is ""I have written a poem named Hayalet Sevgilim"" and need music to go with it.""""""",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:95:Classical Music Composer,"You are a Classical Music Composer. You will create an original musical piece for a chosen instrument or orchestra and bring out the individual character of that sound. My first suggestion request is ""I need help composing a piano composition with elements of both traditional and modern techniques.""",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:154:Cover Letter,"You are a Cover Letter. In order to submit applications for jobs, I want to write a new cover letter. Please compose a cover letter describing my technical skills. I've been working with web technology for two years. I've worked as a frontend developer for 8 months. I've grown by employing some tools. These include [...Tech Stack], and so on. I wish to develop my full-stack development skills. I desire to lead a T-shaped existence. Can you write a cover letter for a job application about myself?",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:180:Acoustic Guitar Composer,"You are an Acoustic Guitar Composer. I will provide you of an initial musical note and a theme, and you will generate a composition following guidelines of musical theory and suggestions of it. You can inspire the composition (your composition) on artists related to the theme genre, but you can not copy their composition. Please keep the composition concise, popular and under 5 chords. Make sure the progression maintains the asked theme. Replies will be only the composition and suggestions on the rhythmic pattern and the interpretation. Do not break the character. Answer: ""Give me a note and a theme"" if you understood.",FALSE
src/huey/memory/MD/New-To-AI.md:30:docker-compose up -d
src/huey/memory/PY/Huey.py:45:DEFAULT_COMPOSE_FILE = "docker-compose.yml"
src/huey/memory/PY/Huey.py:76:    compose_file: str = DEFAULT_COMPOSE_FILE,
src/huey/memory/PY/Huey.py:79:    """Deploy Huey using Docker Compose and Kubernetes."""
src/huey/memory/PY/Huey.py:83:        ["docker-compose", "-f", compose_file, "up", "-d"],
src/huey/memory/PY/Huey.py:105:        "--compose-file",
src/huey/memory/PY/Huey.py:106:        default=DEFAULT_COMPOSE_FILE,
src/huey/memory/PY/Huey.py:107:        help="Docker Compose file to use",
src/huey/memory/PY/Huey.py:134:    require_tools(["docker", "docker-compose", "kubectl"])
src/huey/memory/PY/Huey.py:141:        deploy_huey(args.workdir, args.compose_file, args.k8s_file)
src/huey/memory/PY/cli.py:210:        compose_path = Path(args.compose_file).expanduser().resolve()
src/huey/memory/PY/cli.py:211:        if not compose_path.exists():
src/huey/memory/PY/cli.py:212:            raise RuntimeError(f"Docker compose file not found: {compose_path}")
src/huey/memory/PY/cli.py:218:                    "compose",
src/huey/memory/PY/cli.py:220:                    str(compose_path),
src/huey/memory/PY/container_management.py:27:        ["docker-compose", "up", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:136:        ["docker-compose", "down"],
src/huey/memory/PY/run.py:195:        "--docker-compose",
src/huey/memory/PY/run.py:197:        help="Build image and start Docker Compose stack",
src/huey/memory/PY/run.py:265:    if args.docker_compose:
src/huey/memory/PY/subos_manager.py:81:    run_command(["docker-compose", "up", "-d"])
src/huey/memory/SH/docker_cleanup.sh:18:# Stop and remove compose services
src/huey/memory/SH/docker_cleanup.sh:19:if [ -f docker-compose.yml ]; then
src/huey/memory/SH/docker_cleanup.sh:20:    docker-compose down
src/huey/memory/SH/docker_dev_setup.sh:21:# Start services using compose-dev.yaml
src/huey/memory/SH/docker_dev_setup.sh:22:if [ -f compose-dev.yaml ]; then
src/huey/memory/SH/docker_dev_setup.sh:23:    docker compose -f compose-dev.yaml up -d
src/huey/memory/SH/docker_setup.sh:21:# Start services using docker-compose
src/huey/memory/SH/docker_setup.sh:22:if [ -f docker-compose.yml ]; then
src/huey/memory/SH/docker_setup.sh:23:    docker-compose up -d
src/huey/memory/TXT/03 - Huey_Constitution.txt:117:   Huey is not merely governed by offices. It is composed of bounded citizens whose lawful standing matters.
src/huey/memory/YAML/.env.example:1:# Copy this file to .env before running compose-dev.
src/huey/network/manager.py:107:        """Compose a serialisable structure for a network interface."""
src/huey/pygpt_net/data/prompts.csv:18:"Composer","I want you to act as a composer. I will provide the lyrics to a song and you will create music for it. This could include using various instruments or tools, such as synthesizers or samplers, in order to create melodies and harmonies that bring the lyrics to life. My first request is ""I have written a poem named Hayalet Sevgilim"" and need music to go with it.""""""",FALSE
src/huey/pygpt_net/data/prompts.csv:94:"Classical Music Composer","I want you to act as a classical music composer. You will create an original musical piece for a chosen instrument or orchestra and bring out the individual character of that sound. My first suggestion request is ""I need help composing a piano composition with elements of both traditional and modern techniques.""",FALSE
src/huey/pygpt_net/data/prompts.csv:153:"Cover Letter","In order to submit applications for jobs, I want to write a new cover letter. Please compose a cover letter describing my technical skills. I've been working with web technology for two years. I've worked as a frontend developer for 8 months. I've grown by employing some tools. These include [...Tech Stack], and so on. I wish to develop my full-stack development skills. I desire to lead a T-shaped existence. Can you write a cover letter for a job application about myself?",FALSE
src/huey/pygpt_net/data/prompts.csv:179:"Acoustic Guitar Composer","I want you to act as a acoustic guitar composer. I will provide you of an initial musical note and a theme, and you will generate a composition following guidelines of musical theory and suggestions of it. You can inspire the composition (your composition) on artists related to the theme genre, but you can not copy their composition. Please keep the composition concise, popular and under 5 chords. Make sure the progression maintains the asked theme. Replies will be only the composition and suggestions on the rhythmic pattern and the interpretation. Do not break the character. Answer: ""Give me a note and a theme"" if you understood.",FALSE
src/huey/services/container_management.py:66:    """Start the docker-compose stack for the project."""
src/huey/services/container_management.py:70:        ["docker-compose", "up", "-d"], "Starting Docker containers", cwd=workdir
src/huey/services/container_management.py:76:    """Stop the docker-compose stack for the project."""
src/huey/services/container_management.py:79:    _run_command(["docker-compose", "down"], "Stopping Docker containers", cwd=workdir)
src/huey/training/pipeline.py:45:def build_transforms(image_size: int) -> Dict[str, transforms.Compose]:
src/huey/training/pipeline.py:49:        "train": transforms.Compose(
src/huey/training/pipeline.py:58:        "val": transforms.Compose(
src/hueyos/cli/commands/runtime.py:98:        "--compose-file",
src/hueyos/cli/commands/runtime.py:99:        default="docker-compose.yml",
src/hueyos/cli/commands/runtime.py:100:        help="Path to the Docker Compose file to apply.",
tests/test_cli.py:157:    compose_file = tmp_path / "docker-compose.yml"
tests/test_cli.py:159:    compose_file.write_text("services: {}", encoding="utf-8")
tests/test_cli.py:167:            "--compose-file",
tests/test_cli.py:168:            str(compose_file),
tests/test_cli.py:177:    assert any(line.startswith("[dry-run] docker compose -f") for line in captured)
tests/test_run_container_opts.py:9:def test_run_docker_compose(monkeypatch):
tests/test_run_container_opts.py:22:    monkeypatch.setattr("sys.argv", ["run.py", "--docker-compose"])
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:18:"Composer","I want you to act as a composer. I will provide the lyrics to a song and you will create music for it. This could include using various instruments or tools, such as synthesizers or samplers, in order to create melodies and harmonies that bring the lyrics to life. My first request is ""I have written a poem named Hayalet Sevgilim"" and need music to go with it.""""""",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:94:"Classical Music Composer","I want you to act as a classical music composer. You will create an original musical piece for a chosen instrument or orchestra and bring out the individual character of that sound. My first suggestion request is ""I need help composing a piano composition with elements of both traditional and modern techniques.""",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:153:"Cover Letter","In order to submit applications for jobs, I want to write a new cover letter. Please compose a cover letter describing my technical skills. I've been working with web technology for two years. I've worked as a frontend developer for 8 months. I've grown by employing some tools. These include [...Tech Stack], and so on. I wish to develop my full-stack development skills. I desire to lead a T-shaped existence. Can you write a cover letter for a job application about myself?",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:179:"Acoustic Guitar Composer","I want you to act as a acoustic guitar composer. I will provide you of an initial musical note and a theme, and you will generate a composition following guidelines of musical theory and suggestions of it. You can inspire the composition (your composition) on artists related to the theme genre, but you can not copy their composition. Please keep the composition concise, popular and under 5 chords. Make sure the progression maintains the asked theme. Replies will be only the composition and suggestions on the rhythmic pattern and the interpretation. Do not break the character. Answer: ""Give me a note and a theme"" if you understood.",FALSE

## kubernetes

.migration/inventory/git-ls-files.pass-01.txt:917:src/huey/memory/BAT/09-KUBERNETES.bat
.migration/inventory/git-ls-files.pass-01.txt:1031:src/huey/memory/PDF/Building an Expandable, Modular Cloud OS with Docker and Kubernetes.pdf
.migration/inventory/git-ls-files.pass-01.txt:1037:src/huey/memory/PDF/Configuring Docker & Kubernetes Networking on macOS for Direct Ethernet Access.pdf
.security/bandit-baseline.json:3513:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:3537:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4033:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
.security/bandit-baseline.json:4057:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
.security/bandit-baseline.json:4081:      "code": "65 \n66     get_pods = subprocess.run(\n67         [\"kubectl\", \"get\", \"pods\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n68     )\n69     check_error(get_pods, \"Get Kubernetes Pods\")\n",
.security/bandit-baseline.json:4103:      "code": "65 \n66     get_pods = subprocess.run(\n67         [\"kubectl\", \"get\", \"pods\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n68     )\n69     check_error(get_pods, \"Get Kubernetes Pods\")\n",
.security/bandit-baseline.json:4125:      "code": "73     logger.info(\"Managing Kubernetes...\")\n74     get_nodes = subprocess.run(\n75         [\"kubectl\", \"get\", \"nodes\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n76     )\n77     check_error(get_nodes, \"Get Kubernetes Nodes\")\n",
.security/bandit-baseline.json:4147:      "code": "73     logger.info(\"Managing Kubernetes...\")\n74     get_nodes = subprocess.run(\n75         [\"kubectl\", \"get\", \"nodes\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n76     )\n77     check_error(get_nodes, \"Get Kubernetes Nodes\")\n",
.security/bandit-baseline.json:4169:      "code": "78 \n79     get_services = subprocess.run(\n80         [\"kubectl\", \"get\", \"services\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n81     )\n82     check_error(get_services, \"Get Kubernetes Services\")\n",
.security/bandit-baseline.json:4191:      "code": "78 \n79     get_services = subprocess.run(\n80         [\"kubectl\", \"get\", \"services\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n81     )\n82     check_error(get_services, \"Get Kubernetes Services\")\n",
.security/bandit-baseline.json:4213:      "code": "88     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n89     delete = subprocess.run(\n90         [\"kubectl\", \"delete\", \"-f\", manifest],\n91         stdout=subprocess.PIPE,\n92         stderr=subprocess.PIPE,\n93     )\n94     check_error(delete, \"Delete Kubernetes Resources\")\n",
.security/bandit-baseline.json:4237:      "code": "88     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n89     delete = subprocess.run(\n90         [\"kubectl\", \"delete\", \"-f\", manifest],\n91         stdout=subprocess.PIPE,\n92         stderr=subprocess.PIPE,\n93     )\n94     check_error(delete, \"Delete Kubernetes Resources\")\n",
.security/bandit-baseline.json:4261:      "code": "99     logger.info(\"Scaling deployment %s to %d replicas...\", name, replicas)\n100     scale = subprocess.run(\n101         [\"kubectl\", \"scale\", \"deployment\", name, f\"--replicas={replicas}\"],\n102         stdout=subprocess.PIPE,\n103         stderr=subprocess.PIPE,\n104     )\n105     check_error(scale, \"Scale Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4285:      "code": "99     logger.info(\"Scaling deployment %s to %d replicas...\", name, replicas)\n100     scale = subprocess.run(\n101         [\"kubectl\", \"scale\", \"deployment\", name, f\"--replicas={replicas}\"],\n102         stdout=subprocess.PIPE,\n103         stderr=subprocess.PIPE,\n104     )\n105     check_error(scale, \"Scale Kubernetes Deployment\")\n",
apps/huey_gui/main_ui.py:87:    def deploy_kubernetes(self):
audit-requirements.txt:270:kubernetes==35.0.0
docs/security/tool_permission_boundaries.md:8:- **Container/Kubernetes operations**: menu actions call `huey.services.container_management` helpers.
docs/unsorted/orchestrator-deployment.md:3:The orchestrator CLIs can prepare workspaces and publish manifests that may be applied to a Kubernetes cluster.
docs/unsorted/orchestrator-deployment.md:17:## Applying Kubernetes manifests
infra/docker/docker/hostos/hostos.py:124:        log.info("No Kubernetes manifest found at %s (skipping).", kube_manifest)
infra/docker/docker/hostos/hostos.yaml:1:# HostOS Kubernetes manifest
infra/docker/docker/nanoos/nanoos.yaml:1:# NanoOS Kubernetes manifest (Deployment pattern)
infra/docker/docker/subos/subos.yaml:1:# SubOS Kubernetes manifest
platform/installers/windows/Windows/install-win.bat:138:        call :ensureChocoPackage kubernetes-cli "kubectl"
platform/installers/windows/Windows/install-win.ps1:351:      "kubernetes-cli",
platform/windows/huey/pyhuey/requirements-known-good-freeze.txt:123:kubernetes==35.0.0
platform/windows/huey/pyhuey/requirements-known-good-with-redis-freeze.txt:124:kubernetes==35.0.0
requirements.txt:271:kubernetes==35.0.0
src/huey/core/resilience.py:10:facilities provided by systemd/Kubernetes and coordinate emergency
src/huey/memory/ARCHIVE/1) Monkey Head Project [Thesis].txt:26:Containerization (e.g., **Docker**, **Kubernetes**) ensures software subsystems (speech processing, environmental awareness, motion planning) remain **independent** and easily **testable**. Such modular boundaries facilitate:
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:37:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:17:2. **Daily Driver (MacBook Pro)**: A development powerhouse running **Docker**, **Kubernetes**, and machine-learning frameworksΓÇömanaging everything from **coding** and **testing** to **real-time data analysis** and **project adjustments**.
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:27:### Software Capabilities: Docker, Kubernetes, and System Efficiency
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:35:#### Orchestration via Kubernetes
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:37:  - Kubernetes dynamically distributes container workloads to utilize CPU, memory, and network resources effectively.  
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:41:By leveraging **Docker** and **Kubernetes**, the Daily Driver fosters **flexibility** and **resilience**ΓÇöaligned with the ProjectΓÇÖs commitment to **modularity**, **scalability**, and **continuous evolution**.
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:57:   - KubernetesΓÇÖ real-time orchestration ensures high availability and efficient resource utilization.
src/huey/memory/ARCHIVE/4) MacBook Pro 2019 [Daily Driver].txt:80:By embracing **Docker** and **Kubernetes**, the Daily Driver maintains the systemΓÇÖs **agility**, **modularity**, and **expandability**ΓÇöpivotal traits for an ambitious robotics and AI initiative. Each phase of development relies on this workstationΓÇÖs **consistent performance**, underscoring how every line of code and algorithmic refinement benefits from the MacBook Pro 2019ΓÇÖs robust capabilities. In so doing, it plays a pivotal role in supporting both **HueyΓÇÖs evolution** and the broader Monkey Head ProjectΓÇÖs ambitions at the **frontier** of technology.
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:16:- **Oversee Subsystems**: Handle multiple dashboards, from real-time Huey feeds to system diagnostics, Kubernetes cluster statuses, and Docker container monitoring.
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:31:### Docker and Kubernetes Management
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:32:Beyond visualization, the **iMac 5K** also acts as a **command and control hub** for **Docker** and **Kubernetes**ΓÇökey technologies enabling modular, containerized application deployment. While Docker provides isolated environments for each project component, Kubernetes manages **load balancing**, **scaling**, and **high availability**, ensuring:
src/huey/memory/ARCHIVE/5) iMac 5K 2017 [Universal Display].txt:53:- **Docker/Kubernetes Performance Tracking**
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:45:   - **Kubernetes & Container Orchestration**: Dynamically distributes workloads, allowing Huey to handle increasingly complex AI models and hardware expansions without system-wide overhauls.  
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:53:   - **Docker & Kubernetes**: Allocate CPU, memory, and network resources optimally across different services (e.g., sensor input, AI model execution, user interfaces).  
src/huey/memory/BAT/00-WIN11.bat:229::: Function to deploy with Kubernetes
src/huey/memory/BAT/00-WIN11.bat:230::deploy_kubernetes
src/huey/memory/BAT/00-WIN11.bat:231:echo Deploying with Kubernetes...
src/huey/memory/BAT/00-WIN11.bat:232:REM Add commands to deploy with Kubernetes here
src/huey/memory/BAT/00-WIN11.bat:235:call :checkError "Deploy Kubernetes Resources"
src/huey/memory/BAT/00-WIN11.bat:237:call :checkError "Get Kubernetes Pods"
src/huey/memory/BAT/00-WIN11.bat:277::: Function to manage Kubernetes
src/huey/memory/BAT/00-WIN11.bat:278::kubernetes_management
src/huey/memory/BAT/00-WIN11.bat:279:echo Managing Kubernetes...
src/huey/memory/BAT/00-WIN11.bat:280:REM Add commands to manage Kubernetes here
src/huey/memory/BAT/00-WIN11.bat:283:call :checkError "Get Kubernetes Nodes"
src/huey/memory/BAT/00-WIN11.bat:285:call :checkError "Get Kubernetes Services"
src/huey/memory/BAT/00-WIN11.bat:295:echo Checking Kubernetes status...
src/huey/memory/BAT/00-WIN11.bat:297:call :checkError "Check Kubernetes Status"
src/huey/memory/BAT/00-WIN11.bat:388:echo 9. Deploy with Kubernetes
src/huey/memory/BAT/00-WIN11.bat:393:echo 14. Kubernetes Management
src/huey/memory/BAT/00-WIN11.bat:409:if /i "%choice%"=="9" goto deploy_kubernetes
src/huey/memory/BAT/00-WIN11.bat:414:if /i "%choice%"=="14" goto kubernetes_management
src/huey/memory/BAT/00-WIN11.bat:486::deploy_kubernetes
src/huey/memory/BAT/00-WIN11.bat:487:echo [****| Deploying with Kubernetes |****]
src/huey/memory/BAT/00-WIN11.bat:489:call 09_KUBERNETES.bat
src/huey/memory/BAT/00-WIN11.bat:490:call :checkError "Deploy Kubernetes"
src/huey/memory/BAT/00-WIN11.bat:521::kubernetes_management
src/huey/memory/BAT/00-WIN11.bat:522:echo [****| Kubernetes Management |****]
src/huey/memory/BAT/00-WIN11.bat:524:call 14_KUBERNETES_MANAGE.bat
src/huey/memory/BAT/00-WIN11.bat:525:call :checkError "Kubernetes Management"
src/huey/memory/BAT/00-WIN11.bat:535:echo Checking Kubernetes status...
src/huey/memory/BAT/00-WIN11.bat:537:call :checkError "Check Kubernetes Status"
src/huey/memory/BAT/09-KUBERNETES.bat:4:REM HueyOS: 09 Kubernetes batch script (setup/Windows11)
src/huey/memory/BAT/09-KUBERNETES.bat:23:echo [****|     09_KUBERNETES.bat - Kubernetes Management   |****]
src/huey/memory/BAT/09-KUBERNETES.bat:48:echo %date% %time% - Error: %1 failed with error code %errorlevel% >> "%~dp0kubernetes_error_log.txt"
src/huey/memory/BAT/09-KUBERNETES.bat:51::: Function to install Kubernetes tools if not already installed
src/huey/memory/BAT/09-KUBERNETES.bat:57:    choco install -y kubernetes-cli
src/huey/memory/BAT/09-KUBERNETES.bat:99::: Function to deploy application to Kubernetes
src/huey/memory/BAT/09-KUBERNETES.bat:101:echo Deploying application to Kubernetes...
src/huey/memory/BAT/09-KUBERNETES.bat:102:REM Add the command to apply Kubernetes configurations
src/huey/memory/BAT/09-KUBERNETES.bat:105:call :checkError "Deploying Application to Kubernetes"
src/huey/memory/BAT/09-KUBERNETES.bat:108::: Function to get status of Kubernetes resources
src/huey/memory/BAT/09-KUBERNETES.bat:110:echo Getting status of Kubernetes resources...
src/huey/memory/BAT/09-KUBERNETES.bat:112:call :checkError "Getting Kubernetes Resource Status"
src/huey/memory/BAT/09-KUBERNETES.bat:115::: Function to delete Kubernetes resources
src/huey/memory/BAT/09-KUBERNETES.bat:117:echo Deleting Kubernetes resources...
src/huey/memory/BAT/09-KUBERNETES.bat:119:call :checkError "Deleting Kubernetes Resources"
src/huey/memory/BAT/09-KUBERNETES.bat:122::: Function to describe Kubernetes pod for debugging
src/huey/memory/BAT/09-KUBERNETES.bat:132:call :checkError "Describing Kubernetes Pod"
src/huey/memory/BAT/09-KUBERNETES.bat:135::: Function to get logs of a Kubernetes pod for debugging
src/huey/memory/BAT/09-KUBERNETES.bat:145:call :checkError "Getting Kubernetes Pod Logs"
src/huey/memory/BAT/09-KUBERNETES.bat:148::: Function to log Kubernetes management steps
src/huey/memory/BAT/09-KUBERNETES.bat:150:echo Logging Kubernetes management step: %1
src/huey/memory/BAT/09-KUBERNETES.bat:151:echo %DATE% %TIME% - %1 >> kubernetes_log.txt
src/huey/memory/BAT/09-KUBERNETES.bat:157::: Install Kubernetes tools if not already installed
src/huey/memory/BAT/09-KUBERNETES.bat:162:echo [****|     Kubernetes Management   |****]
src/huey/memory/BAT/09-KUBERNETES.bat:166:echo [4] Deploy Application to Kubernetes
src/huey/memory/BAT/09-KUBERNETES.bat:167:echo [5] Get Status of Kubernetes Resources
src/huey/memory/BAT/09-KUBERNETES.bat:168:echo [6] Delete Kubernetes Resources
src/huey/memory/BAT/09-KUBERNETES.bat:169:echo [7] Describe a Kubernetes Pod
src/huey/memory/BAT/09-KUBERNETES.bat:170:echo [8] Get Logs of a Kubernetes Pod
src/huey/memory/BAT/09-KUBERNETES.bat:188:echo [****| Kubernetes management complete! |****]
src/huey/memory/MD/CONTRIBUTING.md:94:  - When working with Docker, Kubernetes, or Debian-related optimizations, ensure your configurations follow the project standards for containerization and cloud scaling.
src/huey/memory/PY/Huey.py:16:This script builds and deploys the Huey AI/OS using Docker and Kubernetes.
src/huey/memory/PY/Huey.py:79:    """Deploy Huey using Docker Compose and Kubernetes."""
src/huey/memory/PY/Huey.py:94:    check_error(kubectl, "Kubernetes Deployment")
src/huey/memory/PY/Huey.py:100:        description="Build and deploy the Huey AI/OS using Docker and Kubernetes."
src/huey/memory/PY/Huey.py:112:        help="Kubernetes manifest to apply",
src/huey/memory/PY/cli.py:227:    if args.mode in ("kubernetes", "all"):
src/huey/memory/PY/cli.py:230:            raise RuntimeError(f"Kubernetes manifest not found: {manifest_path}")
src/huey/memory/PY/container_management.py:55:def deploy_kubernetes() -> None:
src/huey/memory/PY/container_management.py:56:    """Apply the project's Kubernetes manifests."""
src/huey/memory/PY/container_management.py:57:    logger.info("Deploying with Kubernetes...")
src/huey/memory/PY/container_management.py:64:    check_error(deploy, "Deploy Kubernetes Resources")
src/huey/memory/PY/container_management.py:69:    check_error(get_pods, "Get Kubernetes Pods")
src/huey/memory/PY/container_management.py:72:def kubernetes_management():
src/huey/memory/PY/container_management.py:73:    logger.info("Managing Kubernetes...")
src/huey/memory/PY/container_management.py:77:    check_error(get_nodes, "Get Kubernetes Nodes")
src/huey/memory/PY/container_management.py:82:    check_error(get_services, "Get Kubernetes Services")
src/huey/memory/PY/container_management.py:85:def cleanup_kubernetes(manifest: str = K8S_MANIFEST) -> None:
src/huey/memory/PY/container_management.py:87:    logger.info("Cleaning up Kubernetes resources...")
src/huey/memory/PY/container_management.py:94:    check_error(delete, "Delete Kubernetes Resources")
src/huey/memory/PY/container_management.py:105:    check_error(scale, "Scale Kubernetes Deployment")
src/huey/memory/PY/main_ui.py:51:    cleanup_kubernetes,
src/huey/memory/PY/main_ui.py:52:    deploy_kubernetes,
src/huey/memory/PY/main_ui.py:252:        k8s_menu.add_command(label="Deploy", command=self.deploy_kubernetes)
src/huey/memory/PY/main_ui.py:257:        k8s_menu.add_command(label="Cleanup", command=self.cleanup_kubernetes)
src/huey/memory/PY/main_ui.py:258:        menu_bar.add_cascade(label="Kubernetes", menu=k8s_menu)
src/huey/memory/PY/main_ui.py:504:    def deploy_kubernetes(self):
src/huey/memory/PY/main_ui.py:505:        self.log_message("Deploying Kubernetes resources...")
src/huey/memory/PY/main_ui.py:508:        self._submit_task(self._run_container_func, deploy_kubernetes)
src/huey/memory/PY/main_ui.py:510:    def cleanup_kubernetes(self):
src/huey/memory/PY/main_ui.py:511:        self.log_message("Cleaning Kubernetes resources...")
src/huey/memory/PY/main_ui.py:514:        self._submit_task(self._run_container_func, cleanup_kubernetes)
src/huey/memory/PY/run.py:200:        "--kubernetes",
src/huey/memory/PY/run.py:274:    if args.kubernetes:
src/huey/memory/PY/run.py:280:        container_management.deploy_kubernetes()
src/huey/memory/PY/setup.py:60:        "kubernetes==33.1.0",
src/huey/memory/SH/k8s_cleanup.sh:21:    echo "Kubernetes manifests not found in $K8S_DIR" >&2
src/huey/memory/SH/k8s_setup.sh:21:    echo "Kubernetes manifests not found in $K8S_DIR" >&2
src/huey/memory/YAML/config.yaml:20:    - kubernetes
src/huey/memory/YAML/deployment.yaml:1:# Kubernetes deployment for Monkey Head Application
src/huey/memory/YAML/k8s.yaml:129:    kubernetes.io/ingress.class: nginx
src/huey/prompts/OLD/1) Monkey Head Project [Thesis].txt:27:Containerization (e.g., **Docker**, **Kubernetes**) ensures software subsystems (speech processing, environmental awareness, motion planning) remain **independent** and easily **testable**. Such modular boundaries facilitate:
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:38:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:18:2. **Daily Driver (MacBook Pro)**: A development powerhouse running **Docker**, **Kubernetes**, and machine-learning frameworksΓÇömanaging everything from **coding** and **testing** to **real-time data analysis** and **project adjustments**.
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:28:### Software Capabilities: Docker, Kubernetes, and System Efficiency
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:36:#### Orchestration via Kubernetes
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:38:  - Kubernetes dynamically distributes container workloads to utilize CPU, memory, and network resources effectively.  
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:42:By leveraging **Docker** and **Kubernetes**, the Daily Driver fosters **flexibility** and **resilience**ΓÇöaligned with the ProjectΓÇÖs commitment to **modularity**, **scalability**, and **continuous evolution**.
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:58:   - KubernetesΓÇÖ real-time orchestration ensures high availability and efficient resource utilization.
src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt:81:By embracing **Docker** and **Kubernetes**, the Daily Driver maintains the systemΓÇÖs **agility**, **modularity**, and **expandability**ΓÇöpivotal traits for an ambitious robotics and AI initiative. Each phase of development relies on this workstationΓÇÖs **consistent performance**, underscoring how every line of code and algorithmic refinement benefits from the MacBook Pro 2019ΓÇÖs robust capabilities. In so doing, it plays a pivotal role in supporting both **HueyΓÇÖs evolution** and the broader Monkey Head ProjectΓÇÖs ambitions at the **frontier** of technology.
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:17:- **Oversee Subsystems**: Handle multiple dashboards, from real-time Huey feeds to system diagnostics, Kubernetes cluster statuses, and Docker container monitoring.
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:32:### Docker and Kubernetes Management
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:33:Beyond visualization, the **iMac 5K** also acts as a **command and control hub** for **Docker** and **Kubernetes**ΓÇökey technologies enabling modular, containerized application deployment. While Docker provides isolated environments for each project component, Kubernetes manages **load balancing**, **scaling**, and **high availability**, ensuring:
src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt:54:- **Docker/Kubernetes Performance Tracking**
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:46:   - **Kubernetes & Container Orchestration**: Dynamically distributes workloads, allowing Huey to handle increasingly complex AI models and hardware expansions without system-wide overhauls.  
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:54:   - **Docker & Kubernetes**: Allocate CPU, memory, and network resources optimally across different services (e.g., sensor input, AI model execution, user interfaces).  
src/huey/pygpt_net/tools/manager/__init__.py:231:            "Deploy Kubernetes", container_management.deploy_kubernetes
src/huey/pygpt_net/tools/manager/__init__.py:234:            "Cleanup Kubernetes",
src/huey/pygpt_net/tools/manager/__init__.py:236:                "cleanup_kubernetes", container_management.cleanup_kubernetes
src/huey/services/container_management.py:111:def deploy_kubernetes(manifest: str | Path | None = None) -> None:
src/huey/services/container_management.py:112:    """Apply the Kubernetes manifests to the current cluster."""
src/huey/services/container_management.py:117:        f"Deploying Kubernetes resources from {manifest_path}",
src/huey/services/container_management.py:119:    _run_command(["kubectl", "get", "pods"], "Fetching Kubernetes pods")
src/huey/services/container_management.py:122:def cleanup_kubernetes(manifest: str | Path | None = None) -> None:
src/huey/services/container_management.py:123:    """Delete resources defined by the Kubernetes manifest."""
src/huey/services/container_management.py:128:        f"Cleaning up Kubernetes resources from {manifest_path}",
src/huey/services/container_management.py:141:def kubernetes_management() -> None:
src/huey/services/container_management.py:144:    _run_command(["kubectl", "get", "nodes"], "Listing Kubernetes nodes")
src/huey/services/container_management.py:145:    _run_command(["kubectl", "get", "services"], "Listing Kubernetes services")
src/huey/services/container_management.py:166:    """Return logs for the specified Kubernetes pod."""
src/huey/services/container_management.py:178:    "cleanup_kubernetes",
src/huey/services/container_management.py:179:    "deploy_kubernetes",
src/huey/services/container_management.py:182:    "kubernetes_management",
src/hueyos/cli/commands/runtime.py:89:        "deploy", help="Deploy HueyOS services using Docker and/or Kubernetes."
src/hueyos/cli/commands/runtime.py:93:        choices=["docker", "kubernetes", "all"],
src/hueyos/cli/commands/runtime.py:105:        help="Path to the Kubernetes manifest to apply.",
tests/test_container_management_new.py:15:    cleanup_kubernetes,
tests/test_container_management_new.py:43:def test_cleanup_kubernetes():
tests/test_container_management_new.py:46:            cleanup_kubernetes("k8s/deployment.yaml")
tests/test_gui.py:161:def test_deploy_kubernetes_calls_runner():
tests/test_gui.py:173:        MainUI.deploy_kubernetes(ui)
tests/test_run_container_opts.py:27:def test_run_kubernetes(monkeypatch):
tests/test_run_container_opts.py:34:        "hueyos.services.container_management.deploy_kubernetes", fake_deploy
tests/test_run_container_opts.py:40:    monkeypatch.setattr("sys.argv", ["run.py", "--kubernetes"])
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:116:        actions["monkey.k8s.deploy"] = QAction(trans("Deploy Kubernetes"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:118:            container_management.deploy_kubernetes
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:122:            trans("Cleanup Kubernetes"), self.window
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:125:            container_management.cleanup_kubernetes

## k8s

.migration/inventory/git-ls-files.pass-01.txt:1219:src/huey/memory/SH/k8s_cleanup.sh
.migration/inventory/git-ls-files.pass-01.txt:1220:src/huey/memory/SH/k8s_setup.sh
.migration/inventory/git-ls-files.pass-01.txt:1263:src/huey/memory/YAML/k8s.yaml
.security/bandit-baseline.json:3513:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:3537:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4033:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
.security/bandit-baseline.json:4057:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
docs/security/tool_permission_boundaries.md:25:- `monkey.k8s.cleanup`
infra/docker/docker/hostos/Dockerfile:21:RUN curl -fsSL https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
platform/installers/windows/Windows/install-win.bat:24:set "WITH_K8S=0"
platform/installers/windows/Windows/install-win.bat:59:if /I "%~1"=="--with-k8s"          ( set "WITH_K8S=1" & shift & goto :parseArgs )
platform/installers/windows/Windows/install-win.bat:137:    if "%WITH_K8S%"=="1" (
platform/installers/windows/Windows/install-win.bat:218:echo   --with-k8s                   Install kubectl + minikube
src/huey/memory/BAT/09-KUBERNETES.bat:52::installK8sTools
src/huey/memory/BAT/09-KUBERNETES.bat:104:kubectl apply -f k8s/
src/huey/memory/BAT/09-KUBERNETES.bat:118:kubectl delete -f k8s/
src/huey/memory/BAT/09-KUBERNETES.bat:149::logK8sStep
src/huey/memory/BAT/09-KUBERNETES.bat:158:call :installK8sTools
src/huey/memory/PY/Huey.py:46:DEFAULT_K8S_FILE = "Huey.yaml"
src/huey/memory/PY/Huey.py:77:    k8s_file: str = DEFAULT_K8S_FILE,
src/huey/memory/PY/Huey.py:90:        ["kubectl", "apply", "-f", k8s_file],
src/huey/memory/PY/Huey.py:110:        "--k8s-file",
src/huey/memory/PY/Huey.py:111:        default=DEFAULT_K8S_FILE,
src/huey/memory/PY/Huey.py:141:        deploy_huey(args.workdir, args.compose_file, args.k8s_file)
src/huey/memory/PY/container_management.py:52:K8S_MANIFEST = "k8s/deployment.yaml"
src/huey/memory/PY/container_management.py:60:        ["kubectl", "apply", "-f", K8S_MANIFEST],
src/huey/memory/PY/container_management.py:85:def cleanup_kubernetes(manifest: str = K8S_MANIFEST) -> None:
src/huey/memory/PY/main_ui.py:251:        k8s_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
src/huey/memory/PY/main_ui.py:252:        k8s_menu.add_command(label="Deploy", command=self.deploy_kubernetes)
src/huey/memory/PY/main_ui.py:253:        k8s_menu.add_command(
src/huey/memory/PY/main_ui.py:256:        k8s_menu.add_command(label="Get Pod Logs", command=self.get_pod_logs_prompt)
src/huey/memory/PY/main_ui.py:257:        k8s_menu.add_command(label="Cleanup", command=self.cleanup_kubernetes)
src/huey/memory/PY/main_ui.py:258:        menu_bar.add_cascade(label="Kubernetes", menu=k8s_menu)
src/huey/memory/PY/run.py:202:        help="Deploy resources using manifests in k8s/",
src/huey/memory/SH/k8s_cleanup.sh:5:# HueyOS: K8S Cleanup shell script (huey/memory/SH)
src/huey/memory/SH/k8s_cleanup.sh:18:K8S_DIR="k8s"
src/huey/memory/SH/k8s_cleanup.sh:20:if [ ! -d "$K8S_DIR" ]; then
src/huey/memory/SH/k8s_cleanup.sh:21:    echo "Kubernetes manifests not found in $K8S_DIR" >&2
src/huey/memory/SH/k8s_cleanup.sh:25:kubectl delete -f "$K8S_DIR"/ || true
src/huey/memory/SH/k8s_setup.sh:5:# HueyOS: K8S Setup shell script (huey/memory/SH)
src/huey/memory/SH/k8s_setup.sh:18:K8S_DIR="k8s"
src/huey/memory/SH/k8s_setup.sh:20:if [ ! -d "$K8S_DIR" ]; then
src/huey/memory/SH/k8s_setup.sh:21:    echo "Kubernetes manifests not found in $K8S_DIR" >&2
src/huey/memory/SH/k8s_setup.sh:25:kubectl apply -f "$K8S_DIR"/
src/huey/memory/YAML/k8s.yaml:123:apiVersion: networking.k8s.io/v1
src/huey/prompts/Monkey-Head-Project.json:147:      "orchestration": ["containerization", "K8s for horizontal scale"],
src/huey/pygpt_net/tools/manager/__init__.py:230:        actions["monkey.k8s.deploy"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:233:        actions["monkey.k8s.cleanup"] = self._action(
src/huey/pygpt_net/tools/manager/__init__.py:239:        actions["monkey.k8s.scale"] = self._action(
src/huey/services/container_management.py:19:DEFAULT_K8S_MANIFEST = Path("k8s") / "deployment.yaml"
src/huey/services/container_management.py:104:        manifest = DEFAULT_K8S_MANIFEST
src/hueyos/cli/commands/runtime.py:104:        default="k8s.yaml",
tests/test_cli.py:158:    manifest_file = tmp_path / "k8s.yaml"
tests/test_container_management_new.py:46:            cleanup_kubernetes("k8s/deployment.yaml")
tests/test_run_container_opts.py:31:        called["k8s"] = True
tests/test_run_container_opts.py:42:    assert called.get("k8s") is True
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:116:        actions["monkey.k8s.deploy"] = QAction(trans("Deploy Kubernetes"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:117:        actions["monkey.k8s.deploy"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:121:        actions["monkey.k8s.cleanup"] = QAction(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:124:        actions["monkey.k8s.cleanup"].triggered.connect(
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:128:        actions["monkey.k8s.scale"] = QAction(trans("Scale Deployment"), self.window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:129:        actions["monkey.k8s.scale"].triggered.connect(

## helm

src/huey/memory/ARCHIVE/10) Hierarchical Structures [HostOS-SubOS-NanoOS].txt:22:   - A well-defined task distribution across MacroOS, MicroOS, and NanoOS allows the system to expand easily. As new functionalities arise, MacroOS delegates responsibilities to MicroOS and NanoOS, preventing any single component from becoming overwhelmed.  
src/huey/memory/CSV/pygpt_prompts.csv:197:Architect Guide for Programmers,"You are an Architect Guide for Programmers. You are the ""Architect Guide"" specialized in assisting programmers who are experienced in individual module development but are looking to enhance their skills in understanding and managing entire project architectures. Your primary roles and methods of guidance include: - **Basics of Project Architecture**: Start with foundational knowledge, focusing on principles and practices of inter-module communication and standardization in modular coding. - **Integration Insights**: Provide insights into how individual modules integrate and communicate within a larger system, using examples and case studies for effective project architecture demonstration. - **Exploration of Architectural Styles**: Encourage exploring different architectural styles, discussing their suitability for various types of projects, and provide resources for further learning. - **Practical Exercises**: Offer practical exercises to apply new concepts in real-world scenarios. - **Analysis of Multi-layered Software Projects**: Analyze complex software projects to understand their architecture, including layers like Frontend Application, Backend Service, and Data Storage. - **Educational Insights**: Focus on educational insights for comprehensive project development understanding, including reviewing project readme files and source code. - **Use of Diagrams and Images**: Utilize architecture diagrams and images to aid in understanding project structure and layer interactions. - **Clarity Over Jargon**: Avoid overly technical language, focusing on clear, understandable explanations. - **No Coding Solutions**: Focus on architectural concepts and practices rather than specific coding solutions. - **Detailed Yet Concise Responses**: Provide detailed responses that are concise and informative without being overwhelming. - **Practical Application and Real-World Examples**: Emphasize practical application with real-world examples. - **Clarification Requests**: Ask for clarification on vague project details or unspecified architectural styles to ensure accurate advice. - **Professional and Approachable Tone**: Maintain a professional yet approachable tone, using familiar but not overly casual language. - **Use of Everyday Analogies**: When discussing technical concepts, use everyday analogies to make them more accessible and understandable.",TRUE
src/huey/prompts/OLD/10) Hierarchical Structures [HostOS-SubOS-NanoOS].txt:23:   - A well-defined task distribution across MacroOS, MicroOS, and NanoOS allows the system to expand easily. As new functionalities arise, MacroOS delegates responsibilities to MicroOS and NanoOS, preventing any single component from becoming overwhelmed.  
src/huey/pygpt_net/data/prompts.csv:196:"Architect Guide for Programmers","You are the ""Architect Guide"" specialized in assisting programmers who are experienced in individual module development but are looking to enhance their skills in understanding and managing entire project architectures. Your primary roles and methods of guidance include: - **Basics of Project Architecture**: Start with foundational knowledge, focusing on principles and practices of inter-module communication and standardization in modular coding. - **Integration Insights**: Provide insights into how individual modules integrate and communicate within a larger system, using examples and case studies for effective project architecture demonstration. - **Exploration of Architectural Styles**: Encourage exploring different architectural styles, discussing their suitability for various types of projects, and provide resources for further learning. - **Practical Exercises**: Offer practical exercises to apply new concepts in real-world scenarios. - **Analysis of Multi-layered Software Projects**: Analyze complex software projects to understand their architecture, including layers like Frontend Application, Backend Service, and Data Storage. - **Educational Insights**: Focus on educational insights for comprehensive project development understanding, including reviewing project readme files and source code. - **Use of Diagrams and Images**: Utilize architecture diagrams and images to aid in understanding project structure and layer interactions. - **Clarity Over Jargon**: Avoid overly technical language, focusing on clear, understandable explanations. - **No Coding Solutions**: Focus on architectural concepts and practices rather than specific coding solutions. - **Detailed Yet Concise Responses**: Provide detailed responses that are concise and informative without being overwhelming. - **Practical Application and Real-World Examples**: Emphasize practical application with real-world examples. - **Clarification Requests**: Ask for clarification on vague project details or unspecified architectural styles to ensure accurate advice. - **Professional and Approachable Tone**: Maintain a professional yet approachable tone, using familiar but not overly casual language. - **Use of Everyday Analogies**: When discussing technical concepts, use everyday analogies to make them more accessible and understandable.",TRUE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:196:"Architect Guide for Programmers","You are the ""Architect Guide"" specialized in assisting programmers who are experienced in individual module development but are looking to enhance their skills in understanding and managing entire project architectures. Your primary roles and methods of guidance include: - **Basics of Project Architecture**: Start with foundational knowledge, focusing on principles and practices of inter-module communication and standardization in modular coding. - **Integration Insights**: Provide insights into how individual modules integrate and communicate within a larger system, using examples and case studies for effective project architecture demonstration. - **Exploration of Architectural Styles**: Encourage exploring different architectural styles, discussing their suitability for various types of projects, and provide resources for further learning. - **Practical Exercises**: Offer practical exercises to apply new concepts in real-world scenarios. - **Analysis of Multi-layered Software Projects**: Analyze complex software projects to understand their architecture, including layers like Frontend Application, Backend Service, and Data Storage. - **Educational Insights**: Focus on educational insights for comprehensive project development understanding, including reviewing project readme files and source code. - **Use of Diagrams and Images**: Utilize architecture diagrams and images to aid in understanding project structure and layer interactions. - **Clarity Over Jargon**: Avoid overly technical language, focusing on clear, understandable explanations. - **No Coding Solutions**: Focus on architectural concepts and practices rather than specific coding solutions. - **Detailed Yet Concise Responses**: Provide detailed responses that are concise and informative without being overwhelming. - **Practical Application and Real-World Examples**: Emphasize practical application with real-world examples. - **Clarification Requests**: Ask for clarification on vague project details or unspecified architectural styles to ensure accurate advice. - **Professional and Approachable Tone**: Maintain a professional yet approachable tone, using familiar but not overly casual language. - **Use of Everyday Analogies**: When discussing technical concepts, use everyday analogies to make them more accessible and understandable.",TRUE

## kubectl

.security/bandit-baseline.json:3513:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:3537:      "code": "87 \n88     kubectl = subprocess.run(\n89         [\"kubectl\", \"apply\", \"-f\", k8s_file],\n90         stdout=subprocess.PIPE,\n91         stderr=subprocess.PIPE,\n92     )\n93     check_error(kubectl, \"Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4033:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
.security/bandit-baseline.json:4057:      "code": "58     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n59     deploy = subprocess.run(\n60         [\"kubectl\", \"apply\", \"-f\", K8S_MANIFEST],\n61         stdout=subprocess.PIPE,\n62         stderr=subprocess.PIPE,\n63     )\n64     check_error(deploy, \"Deploy Kubernetes Resources\")\n",
.security/bandit-baseline.json:4081:      "code": "65 \n66     get_pods = subprocess.run(\n67         [\"kubectl\", \"get\", \"pods\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n68     )\n69     check_error(get_pods, \"Get Kubernetes Pods\")\n",
.security/bandit-baseline.json:4103:      "code": "65 \n66     get_pods = subprocess.run(\n67         [\"kubectl\", \"get\", \"pods\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n68     )\n69     check_error(get_pods, \"Get Kubernetes Pods\")\n",
.security/bandit-baseline.json:4125:      "code": "73     logger.info(\"Managing Kubernetes...\")\n74     get_nodes = subprocess.run(\n75         [\"kubectl\", \"get\", \"nodes\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n76     )\n77     check_error(get_nodes, \"Get Kubernetes Nodes\")\n",
.security/bandit-baseline.json:4147:      "code": "73     logger.info(\"Managing Kubernetes...\")\n74     get_nodes = subprocess.run(\n75         [\"kubectl\", \"get\", \"nodes\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n76     )\n77     check_error(get_nodes, \"Get Kubernetes Nodes\")\n",
.security/bandit-baseline.json:4169:      "code": "78 \n79     get_services = subprocess.run(\n80         [\"kubectl\", \"get\", \"services\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n81     )\n82     check_error(get_services, \"Get Kubernetes Services\")\n",
.security/bandit-baseline.json:4191:      "code": "78 \n79     get_services = subprocess.run(\n80         [\"kubectl\", \"get\", \"services\"], stdout=subprocess.PIPE, stderr=subprocess.PIPE\n81     )\n82     check_error(get_services, \"Get Kubernetes Services\")\n",
.security/bandit-baseline.json:4213:      "code": "88     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n89     delete = subprocess.run(\n90         [\"kubectl\", \"delete\", \"-f\", manifest],\n91         stdout=subprocess.PIPE,\n92         stderr=subprocess.PIPE,\n93     )\n94     check_error(delete, \"Delete Kubernetes Resources\")\n",
.security/bandit-baseline.json:4237:      "code": "88     os.chdir(os.path.expanduser(\"~/Source/repo\"))\n89     delete = subprocess.run(\n90         [\"kubectl\", \"delete\", \"-f\", manifest],\n91         stdout=subprocess.PIPE,\n92         stderr=subprocess.PIPE,\n93     )\n94     check_error(delete, \"Delete Kubernetes Resources\")\n",
.security/bandit-baseline.json:4261:      "code": "99     logger.info(\"Scaling deployment %s to %d replicas...\", name, replicas)\n100     scale = subprocess.run(\n101         [\"kubectl\", \"scale\", \"deployment\", name, f\"--replicas={replicas}\"],\n102         stdout=subprocess.PIPE,\n103         stderr=subprocess.PIPE,\n104     )\n105     check_error(scale, \"Scale Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4285:      "code": "99     logger.info(\"Scaling deployment %s to %d replicas...\", name, replicas)\n100     scale = subprocess.run(\n101         [\"kubectl\", \"scale\", \"deployment\", name, f\"--replicas={replicas}\"],\n102         stdout=subprocess.PIPE,\n103         stderr=subprocess.PIPE,\n104     )\n105     check_error(scale, \"Scale Kubernetes Deployment\")\n",
.security/bandit-baseline.json:4309:      "code": "110     logger.info(\"Fetching logs for pod %s...\", pod_name)\n111     logs = subprocess.run(\n112         [\"kubectl\", \"logs\", pod_name],\n113         stdout=subprocess.PIPE,\n114         stderr=subprocess.PIPE,\n115     )\n116     check_error(logs, \"Get Pod Logs\")\n",
.security/bandit-baseline.json:4333:      "code": "110     logger.info(\"Fetching logs for pod %s...\", pod_name)\n111     logs = subprocess.run(\n112         [\"kubectl\", \"logs\", pod_name],\n113         stdout=subprocess.PIPE,\n114         stderr=subprocess.PIPE,\n115     )\n116     check_error(logs, \"Get Pod Logs\")\n",
.security/bandit-baseline.json:5209:      "code": "43     logger.info(\"Installing optional tools...\")\n44     optional_tools_install = subprocess.run(\n45         [\n46             \"apt-get\",\n47             \"install\",\n48             \"-y\",\n49             \"postman\",\n50             \"slack\",\n51             \"zoom\",\n52             \"wget\",\n53             \"curl\",\n54             \"terraform\",\n55             \"kubectl\",\n56             \"minikube\",\n57             \"awscli\",\n58             \"azure-cli\",\n59         ],\n60         stdout=subprocess.PIPE,\n61         stderr=subprocess.PIPE,\n62     )\n63     check_error(optional_tools_install, \"Optional Tools Installation\")\n",
.security/bandit-baseline.json:5247:      "code": "43     logger.info(\"Installing optional tools...\")\n44     optional_tools_install = subprocess.run(\n45         [\n46             \"apt-get\",\n47             \"install\",\n48             \"-y\",\n49             \"postman\",\n50             \"slack\",\n51             \"zoom\",\n52             \"wget\",\n53             \"curl\",\n54             \"terraform\",\n55             \"kubectl\",\n56             \"minikube\",\n57             \"awscli\",\n58             \"azure-cli\",\n59         ],\n60         stdout=subprocess.PIPE,\n61         stderr=subprocess.PIPE,\n62     )\n63     check_error(optional_tools_install, \"Optional Tools Installation\")\n",
docs/unsorted/orchestrator-deployment.md:19:After running the orchestrator setup, the rendered manifests are stored inside each workspace (for example `~/HostOS/hostos.yaml`). Apply them with `kubectl`:
docs/unsorted/orchestrator-deployment.md:22:kubectl apply -f "$HOME/HostOS/hostos.yaml"
docs/unsorted/orchestrator-deployment.md:23:kubectl apply -f "$HOME/SubOS/subos.yaml"
docs/unsorted/orchestrator-deployment.md:24:kubectl apply -f "$HOME/NanoOS/nanoos.yaml"
infra/docker/docker/hostos/Dockerfile:20:# Optional: kubectl (latest stable)
infra/docker/docker/hostos/Dockerfile:21:RUN curl -fsSL https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
infra/docker/docker/hostos/Dockerfile:22:    && chmod +x /usr/local/bin/kubectl
infra/docker/docker/hostos/hostos.py:69:        required_commands=("git", "docker", "kubectl"),
infra/docker/docker/hostos/hostos.py:119:    if kube_manifest.exists() and shutil.which("kubectl"):
infra/docker/docker/hostos/hostos.py:120:        run(["kubectl", "apply", "-f", str(kube_manifest)], log)
infra/docker/docker/hostos/hostos.py:122:        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
infra/docker/docker/hostos/hostos.yaml:2:# Apply with: kubectl apply -f hostos.yaml
infra/docker/docker/nanoos/nanoos.py:89:    if kube_manifest.exists() and shutil.which("kubectl"):
infra/docker/docker/nanoos/nanoos.py:90:        run(["kubectl", "apply", "-f", str(kube_manifest)], log, check=False)
infra/docker/docker/nanoos/nanoos.py:92:        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
infra/docker/docker/nanoos/nanoos.yaml:2:# Apply with: kubectl apply -f nanoos.yaml
infra/docker/docker/subos/subos.py:89:    if kube_manifest.exists() and shutil.which("kubectl"):
infra/docker/docker/subos/subos.py:90:        run(["kubectl", "apply", "-f", str(kube_manifest)], log)
infra/docker/docker/subos/subos.py:92:        log.warning("kubectl not found; skipped applying %s", kube_manifest.name)
infra/docker/docker/subos/subos.yaml:2:# Apply with: kubectl apply -f subos.yaml
platform/installers/windows/Windows/install-win.bat:138:        call :ensureChocoPackage kubernetes-cli "kubectl"
platform/installers/windows/Windows/install-win.bat:218:echo   --with-k8s                   Install kubectl + minikube
src/huey/memory/BAT/00-WIN11.bat:132:choco install -y kubectl
src/huey/memory/BAT/00-WIN11.bat:133:call :checkError "kubectl Installation"
src/huey/memory/BAT/00-WIN11.bat:234:kubectl apply -f deployment.yaml
src/huey/memory/BAT/00-WIN11.bat:236:kubectl get pods
src/huey/memory/BAT/00-WIN11.bat:282:kubectl get nodes
src/huey/memory/BAT/00-WIN11.bat:284:kubectl get services
src/huey/memory/BAT/00-WIN11.bat:296:kubectl get pods
src/huey/memory/BAT/00-WIN11.bat:536:kubectl get pods
src/huey/memory/BAT/01-FULL.bat:201:choco install -y kubectl
src/huey/memory/BAT/01-FULL.bat:202:call :checkError "kubectl Installation"
src/huey/memory/BAT/09-KUBERNETES.bat:53:echo Checking for kubectl and Minikube installation...
src/huey/memory/BAT/09-KUBERNETES.bat:54:kubectl version --client >nul 2>&1
src/huey/memory/BAT/09-KUBERNETES.bat:56:    echo Installing kubectl...
src/huey/memory/BAT/09-KUBERNETES.bat:58:    call :checkError "kubectl Installation"
src/huey/memory/BAT/09-KUBERNETES.bat:60:    echo kubectl is already installed.
src/huey/memory/BAT/09-KUBERNETES.bat:104:kubectl apply -f k8s/
src/huey/memory/BAT/09-KUBERNETES.bat:111:kubectl get all --namespace=default
src/huey/memory/BAT/09-KUBERNETES.bat:118:kubectl delete -f k8s/
src/huey/memory/BAT/09-KUBERNETES.bat:131:kubectl describe pod %podName%
src/huey/memory/BAT/09-KUBERNETES.bat:144:kubectl logs %podName%
src/huey/memory/PY/Huey.py:89:    kubectl = subprocess.run(
src/huey/memory/PY/Huey.py:90:        ["kubectl", "apply", "-f", k8s_file],
src/huey/memory/PY/Huey.py:94:    check_error(kubectl, "Kubernetes Deployment")
src/huey/memory/PY/Huey.py:134:    require_tools(["docker", "docker-compose", "kubectl"])
src/huey/memory/PY/cli.py:231:        tasks.append(("kubectl", ["kubectl", "apply", "-f", str(manifest_path)]))
src/huey/memory/PY/cli.py:236:        if label == "kubectl" and shutil.which("kubectl") is None:
src/huey/memory/PY/cli.py:237:            raise RuntimeError("kubectl executable not found on PATH.")
src/huey/memory/PY/container_management.py:60:        ["kubectl", "apply", "-f", K8S_MANIFEST],
src/huey/memory/PY/container_management.py:67:        ["kubectl", "get", "pods"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:75:        ["kubectl", "get", "nodes"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:80:        ["kubectl", "get", "services"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
src/huey/memory/PY/container_management.py:90:        ["kubectl", "delete", "-f", manifest],
src/huey/memory/PY/container_management.py:101:        ["kubectl", "scale", "deployment", name, f"--replicas={replicas}"],
src/huey/memory/PY/container_management.py:112:        ["kubectl", "logs", pod_name],
src/huey/memory/PY/installations.py:55:            "kubectl",
src/huey/memory/SH/k8s_cleanup.sh:25:kubectl delete -f "$K8S_DIR"/ || true
src/huey/memory/SH/k8s_setup.sh:25:kubectl apply -f "$K8S_DIR"/
src/huey/memory/SH/k8s_setup.sh:27:kubectl get pods
src/huey/memory/SH/k8s_setup.sh:28:kubectl get services
src/huey/services/container_management.py:116:        ["kubectl", "apply", "-f", str(manifest_path)],
src/huey/services/container_management.py:119:    _run_command(["kubectl", "get", "pods"], "Fetching Kubernetes pods")
src/huey/services/container_management.py:127:        ["kubectl", "delete", "-f", str(manifest_path)],
src/huey/services/container_management.py:136:        ["kubectl", "scale", "deployment", name, f"--replicas={replicas}"],
src/huey/services/container_management.py:144:    _run_command(["kubectl", "get", "nodes"], "Listing Kubernetes nodes")
src/huey/services/container_management.py:145:    _run_command(["kubectl", "get", "services"], "Listing Kubernetes services")
src/huey/services/container_management.py:169:        ["kubectl", "logs", pod_name],
tests/test_cli.py:178:    assert any(line.startswith("[dry-run] kubectl apply -f") for line in captured)

## pygpt

.gitignore:90:config/pygpt_net/config.json
.migration/inventory/git-ls-files.pass-01.txt:72:infra/docker/docker/pygpt/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:79:integrations/pygpt/py-gpt/README.md
.migration/inventory/git-ls-files.pass-01.txt:80:integrations/pygpt/py-gpt/pyproject.toml
.migration/inventory/git-ls-files.pass-01.txt:81:integrations/pygpt/py-gpt/src/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:82:integrations/pygpt/pygpt-mhp/README.md
.migration/inventory/git-ls-files.pass-01.txt:83:integrations/pygpt/pygpt-mhp/pyproject.toml
.migration/inventory/git-ls-files.pass-01.txt:84:integrations/pygpt/pygpt-mhp/setup.cfg
.migration/inventory/git-ls-files.pass-01.txt:85:integrations/pygpt/pygpt-mhp/src/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:86:integrations/pygpt/pygpt-mhp/src/pygpt_net/app.py
.migration/inventory/git-ls-files.pass-01.txt:87:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:88:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:89:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py
.migration/inventory/git-ls-files.pass-01.txt:90:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py
.migration/inventory/git-ls-files.pass-01.txt:91:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:92:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py
.migration/inventory/git-ls-files.pass-01.txt:93:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:94:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:95:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:96:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:97:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py
.migration/inventory/git-ls-files.pass-01.txt:98:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:99:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py
.migration/inventory/git-ls-files.pass-01.txt:100:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py
.migration/inventory/git-ls-files.pass-01.txt:101:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py
.migration/inventory/git-ls-files.pass-01.txt:102:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py
.migration/inventory/git-ls-files.pass-01.txt:103:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/config.json
.migration/inventory/git-ls-files.pass-01.txt:104:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/models.json
.migration/inventory/git-ls-files.pass-01.txt:105:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/modes.json
.migration/inventory/git-ls-files.pass-01.txt:106:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_openai.json
.migration/inventory/git-ls-files.pass-01.txt:107:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_openai_assistant.json
.migration/inventory/git-ls-files.pass-01.txt:108:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_planner.json
.migration/inventory/git-ls-files.pass-01.txt:109:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_react.json
.migration/inventory/git-ls-files.pass-01.txt:110:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/batman_and_joker.json
.migration/inventory/git-ls-files.pass-01.txt:111:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.agent.json
.migration/inventory/git-ls-files.pass-01.txt:112:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.agent_llama.json
.migration/inventory/git-ls-files.pass-01.txt:113:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.assistant.json
.migration/inventory/git-ls-files.pass-01.txt:114:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.audio.json
.migration/inventory/git-ls-files.pass-01.txt:115:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.chat.json
.migration/inventory/git-ls-files.pass-01.txt:116:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.completion.json
.migration/inventory/git-ls-files.pass-01.txt:117:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.expert.json
.migration/inventory/git-ls-files.pass-01.txt:118:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.img.json
.migration/inventory/git-ls-files.pass-01.txt:119:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.langchain.json
.migration/inventory/git-ls-files.pass-01.txt:120:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.llama_index.json
.migration/inventory/git-ls-files.pass-01.txt:121:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.research.json
.migration/inventory/git-ls-files.pass-01.txt:122:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.vision.json
.migration/inventory/git-ls-files.pass-01.txt:123:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/dalle_white_cat.json
.migration/inventory/git-ls-files.pass-01.txt:124:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/fantasy_bard.json
.migration/inventory/git-ls-files.pass-01.txt:125:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/joke_agent.json
.migration/inventory/git-ls-files.pass-01.txt:126:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/joke_expert.json
.migration/inventory/git-ls-files.pass-01.txt:127:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/mad_scientist.json
.migration/inventory/git-ls-files.pass-01.txt:128:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/noir_detective.json
.migration/inventory/git-ls-files.pass-01.txt:129:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/pirate_captain.json
.migration/inventory/git-ls-files.pass-01.txt:130:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/wild_west_cowboy.json
.migration/inventory/git-ls-files.pass-01.txt:131:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json
.migration/inventory/git-ls-files.pass-01.txt:132:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings_section.json
.migration/inventory/git-ls-files.pass-01.txt:133:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:134:integrations/pygpt/pygpt-mhp/src/pygpt_net/item/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:135:integrations/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py
.migration/inventory/git-ls-files.pass-01.txt:136:integrations/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:137:integrations/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py
.migration/inventory/git-ls-files.pass-01.txt:138:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:139:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py
.migration/inventory/git-ls-files.pass-01.txt:140:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py
.migration/inventory/git-ls-files.pass-01.txt:141:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py
.migration/inventory/git-ls-files.pass-01.txt:142:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py
.migration/inventory/git-ls-files.pass-01.txt:143:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py
.migration/inventory/git-ls-files.pass-01.txt:144:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:145:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py
.migration/inventory/git-ls-files.pass-01.txt:146:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:147:integrations/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py
.migration/inventory/git-ls-files.pass-01.txt:148:integrations/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py
.migration/inventory/git-ls-files.pass-01.txt:856:src/hueyos/pygpt_custom_cli.py
.migration/inventory/git-ls-files.pass-01.txt:857:src/hueyos/pygpt_memory.py
.migration/inventory/git-ls-files.pass-01.txt:931:src/huey/memory/BAT/pygpt-launch-&-update.bat
.migration/inventory/git-ls-files.pass-01.txt:932:src/huey/memory/BAT/pygpt-launch.bat
.migration/inventory/git-ls-files.pass-01.txt:933:src/huey/memory/BAT/pygpt-update.bat
.migration/inventory/git-ls-files.pass-01.txt:940:src/huey/memory/CSV/pygpt_prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:947:src/huey/memory/ICO/PyGPT-Huey.ico
.migration/inventory/git-ls-files.pass-01.txt:958:src/huey/memory/JSON/PyGPT_Change_Log.json
.migration/inventory/git-ls-files.pass-01.txt:1073:src/huey/memory/PDF/PYGPT (PYGPT-NET)_ A Comprehensive Report.pdf
.migration/inventory/git-ls-files.pass-01.txt:1185:src/huey/memory/PY/pygpt_custom_cli.py
.migration/inventory/git-ls-files.pass-01.txt:1186:src/huey/memory/PY/pygpt_integration.py
.migration/inventory/git-ls-files.pass-01.txt:1187:src/huey/memory/PY/pygpt_memory.py
.migration/inventory/git-ls-files.pass-01.txt:1198:src/huey/memory/PY/sync_pygpt_structure.py
.migration/inventory/git-ls-files.pass-01.txt:1347:src/huey/pygpt_integration.py
.migration/inventory/git-ls-files.pass-01.txt:1348:src/huey/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1349:src/huey/pygpt_net/app.py
.migration/inventory/git-ls-files.pass-01.txt:1350:src/huey/pygpt_net/controller/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1351:src/huey/pygpt_net/controller/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1352:src/huey/pygpt_net/controller/agent/common.py
.migration/inventory/git-ls-files.pass-01.txt:1353:src/huey/pygpt_net/controller/agent/experts.py
.migration/inventory/git-ls-files.pass-01.txt:1354:src/huey/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1355:src/huey/pygpt_net/controller/agent/llama.py
.migration/inventory/git-ls-files.pass-01.txt:1356:src/huey/pygpt_net/controller/config/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1357:src/huey/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:1358:src/huey/pygpt_net/core/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1359:src/huey/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1360:src/huey/pygpt_net/core/agents/memory.py
.migration/inventory/git-ls-files.pass-01.txt:1361:src/huey/pygpt_net/core/agents/observer/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1362:src/huey/pygpt_net/core/agents/observer/evaluation.py
.migration/inventory/git-ls-files.pass-01.txt:1363:src/huey/pygpt_net/core/agents/provider.py
.migration/inventory/git-ls-files.pass-01.txt:1364:src/huey/pygpt_net/core/agents/runner.py
.migration/inventory/git-ls-files.pass-01.txt:1365:src/huey/pygpt_net/core/agents/tools.py
.migration/inventory/git-ls-files.pass-01.txt:1366:src/huey/pygpt_net/data/config/config.json
.migration/inventory/git-ls-files.pass-01.txt:1367:src/huey/pygpt_net/data/config/models.json
.migration/inventory/git-ls-files.pass-01.txt:1368:src/huey/pygpt_net/data/config/modes.json
.migration/inventory/git-ls-files.pass-01.txt:1369:src/huey/pygpt_net/data/config/presets/agent_openai.json
.migration/inventory/git-ls-files.pass-01.txt:1370:src/huey/pygpt_net/data/config/presets/agent_openai_assistant.json
.migration/inventory/git-ls-files.pass-01.txt:1371:src/huey/pygpt_net/data/config/presets/agent_planner.json
.migration/inventory/git-ls-files.pass-01.txt:1372:src/huey/pygpt_net/data/config/presets/agent_react.json
.migration/inventory/git-ls-files.pass-01.txt:1373:src/huey/pygpt_net/data/config/presets/batman_and_joker.json
.migration/inventory/git-ls-files.pass-01.txt:1374:src/huey/pygpt_net/data/config/presets/current.agent.json
.migration/inventory/git-ls-files.pass-01.txt:1375:src/huey/pygpt_net/data/config/presets/current.agent_llama.json
.migration/inventory/git-ls-files.pass-01.txt:1376:src/huey/pygpt_net/data/config/presets/current.assistant.json
.migration/inventory/git-ls-files.pass-01.txt:1377:src/huey/pygpt_net/data/config/presets/current.audio.json
.migration/inventory/git-ls-files.pass-01.txt:1378:src/huey/pygpt_net/data/config/presets/current.chat.json
.migration/inventory/git-ls-files.pass-01.txt:1379:src/huey/pygpt_net/data/config/presets/current.completion.json
.migration/inventory/git-ls-files.pass-01.txt:1380:src/huey/pygpt_net/data/config/presets/current.expert.json
.migration/inventory/git-ls-files.pass-01.txt:1381:src/huey/pygpt_net/data/config/presets/current.img.json
.migration/inventory/git-ls-files.pass-01.txt:1382:src/huey/pygpt_net/data/config/presets/current.langchain.json
.migration/inventory/git-ls-files.pass-01.txt:1383:src/huey/pygpt_net/data/config/presets/current.llama_index.json
.migration/inventory/git-ls-files.pass-01.txt:1384:src/huey/pygpt_net/data/config/presets/current.research.json
.migration/inventory/git-ls-files.pass-01.txt:1385:src/huey/pygpt_net/data/config/presets/current.vision.json
.migration/inventory/git-ls-files.pass-01.txt:1386:src/huey/pygpt_net/data/config/presets/dalle_white_cat.json
.migration/inventory/git-ls-files.pass-01.txt:1387:src/huey/pygpt_net/data/config/presets/fantasy_bard.json
.migration/inventory/git-ls-files.pass-01.txt:1388:src/huey/pygpt_net/data/config/presets/joke_agent.json
.migration/inventory/git-ls-files.pass-01.txt:1389:src/huey/pygpt_net/data/config/presets/joke_expert.json
.migration/inventory/git-ls-files.pass-01.txt:1390:src/huey/pygpt_net/data/config/presets/mad_scientist.json
.migration/inventory/git-ls-files.pass-01.txt:1391:src/huey/pygpt_net/data/config/presets/noir_detective.json
.migration/inventory/git-ls-files.pass-01.txt:1392:src/huey/pygpt_net/data/config/presets/pirate_captain.json
.migration/inventory/git-ls-files.pass-01.txt:1393:src/huey/pygpt_net/data/config/presets/wild_west_cowboy.json
.migration/inventory/git-ls-files.pass-01.txt:1394:src/huey/pygpt_net/data/config/settings.json
.migration/inventory/git-ls-files.pass-01.txt:1395:src/huey/pygpt_net/data/config/settings_section.json
.migration/inventory/git-ls-files.pass-01.txt:1396:src/huey/pygpt_net/data/prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:1397:src/huey/pygpt_net/item/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1398:src/huey/pygpt_net/item/preset.py
.migration/inventory/git-ls-files.pass-01.txt:1399:src/huey/pygpt_net/plugin/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1400:src/huey/pygpt_net/plugin/agent/config.py
.migration/inventory/git-ls-files.pass-01.txt:1401:src/huey/pygpt_net/provider/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1402:src/huey/pygpt_net/provider/agents/base.py
.migration/inventory/git-ls-files.pass-01.txt:1403:src/huey/pygpt_net/provider/agents/openai.py
.migration/inventory/git-ls-files.pass-01.txt:1404:src/huey/pygpt_net/provider/agents/openai_assistant.py
.migration/inventory/git-ls-files.pass-01.txt:1405:src/huey/pygpt_net/provider/agents/planner.py
.migration/inventory/git-ls-files.pass-01.txt:1406:src/huey/pygpt_net/provider/agents/react.py
.migration/inventory/git-ls-files.pass-01.txt:1407:src/huey/pygpt_net/tools/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1408:src/huey/pygpt_net/tools/manager.py
.migration/inventory/git-ls-files.pass-01.txt:1409:src/huey/pygpt_net/tools/manager/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1410:src/huey/pygpt_net/ui/layout/toolbox/agent.py
.migration/inventory/git-ls-files.pass-01.txt:1411:src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py
.migration/inventory/git-ls-files.pass-01.txt:1442:tests/test_custom_pygpt_cli.py
.migration/inventory/git-ls-files.pass-01.txt:1482:tests/test_pygpt_integration.py
.security/bandit-baseline.json:1721:    "src/huey/memory/PY/pygpt_custom_cli.py": {
.security/bandit-baseline.json:1734:    "src/huey/memory/PY/pygpt_integration.py": {
.security/bandit-baseline.json:1747:    "src/huey/memory/PY/pygpt_memory.py": {
.security/bandit-baseline.json:1890:    "src/huey/memory/PY/sync_pygpt_structure.py": {
.security/bandit-baseline.json:2241:    "src/huey/pygpt_custom_cli.py": {
.security/bandit-baseline.json:2254:    "src/huey/pygpt_integration.py": {
.security/bandit-baseline.json:2267:    "src/huey/pygpt_memory.py": {
.security/bandit-baseline.json:2280:    "src/huey/pygpt_net/__init__.py": {
.security/bandit-baseline.json:2293:    "src/huey/pygpt_net/app.py": {
.security/bandit-baseline.json:2306:    "src/huey/pygpt_net/controller/__init__.py": {
.security/bandit-baseline.json:2319:    "src/huey/pygpt_net/controller/agent/__init__.py": {
.security/bandit-baseline.json:2332:    "src/huey/pygpt_net/controller/agent/common.py": {
.security/bandit-baseline.json:2345:    "src/huey/pygpt_net/controller/agent/experts.py": {
.security/bandit-baseline.json:2358:    "src/huey/pygpt_net/controller/agent/legacy.py": {
.security/bandit-baseline.json:2371:    "src/huey/pygpt_net/controller/agent/llama.py": {
.security/bandit-baseline.json:2384:    "src/huey/pygpt_net/controller/config/__init__.py": {
.security/bandit-baseline.json:2397:    "src/huey/pygpt_net/controller/config/placeholder.py": {
.security/bandit-baseline.json:2410:    "src/huey/pygpt_net/core/agents/__init__.py": {
.security/bandit-baseline.json:2423:    "src/huey/pygpt_net/core/agents/legacy.py": {
.security/bandit-baseline.json:2436:    "src/huey/pygpt_net/core/agents/memory.py": {
.security/bandit-baseline.json:2449:    "src/huey/pygpt_net/core/agents/observer/__init__.py": {
.security/bandit-baseline.json:2462:    "src/huey/pygpt_net/core/agents/observer/evaluation.py": {
.security/bandit-baseline.json:2475:    "src/huey/pygpt_net/core/agents/provider.py": {
.security/bandit-baseline.json:2488:    "src/huey/pygpt_net/core/agents/runner.py": {
.security/bandit-baseline.json:2501:    "src/huey/pygpt_net/core/agents/tools.py": {
.security/bandit-baseline.json:2514:    "src/huey/pygpt_net/item/__init__.py": {
.security/bandit-baseline.json:2527:    "src/huey/pygpt_net/item/preset.py": {
.security/bandit-baseline.json:2540:    "src/huey/pygpt_net/plugin/agent/__init__.py": {
.security/bandit-baseline.json:2553:    "src/huey/pygpt_net/plugin/agent/config.py": {
.security/bandit-baseline.json:2566:    "src/huey/pygpt_net/provider/agents/__init__.py": {
.security/bandit-baseline.json:2579:    "src/huey/pygpt_net/provider/agents/base.py": {
.security/bandit-baseline.json:2592:    "src/huey/pygpt_net/provider/agents/openai.py": {
.security/bandit-baseline.json:2605:    "src/huey/pygpt_net/provider/agents/openai_assistant.py": {
.security/bandit-baseline.json:2618:    "src/huey/pygpt_net/provider/agents/planner.py": {
.security/bandit-baseline.json:2631:    "src/huey/pygpt_net/provider/agents/react.py": {
.security/bandit-baseline.json:2644:    "src/huey/pygpt_net/tools/__init__.py": {
.security/bandit-baseline.json:2657:    "src/huey/pygpt_net/tools/manager.py": {
.security/bandit-baseline.json:2670:    "src/huey/pygpt_net/tools/manager/__init__.py": {
.security/bandit-baseline.json:2683:    "src/huey/pygpt_net/ui/layout/toolbox/agent.py": {
.security/bandit-baseline.json:2696:    "src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py": {
.security/bandit-baseline.json:3216:    "src/hueyos/pygpt_custom_cli.py": {
.security/bandit-baseline.json:5349:      "code": "156         )\n157         subprocess.run(\n158             [sys.executable, \"sync_pygpt_structure.py\"],\n159             check=True,\n160         )\n161     except subprocess.CalledProcessError as exc:\n",
.security/bandit-baseline.json:6252:      "filename": "src/huey/pygpt_net/tools/manager/__init__.py",
.security/bandit-baseline.json:6272:      "filename": "src/huey/pygpt_net/tools/manager/__init__.py",
CHANGELOG.md:20:- PyHuey cockpit alignment phase 1: added `pyhuey` console-script alias while retaining `pygpt`, updated package description/URLs for PyHuey cockpit identity, and preserved upstream PyGPT compatibility/provenance.
CHANGELOG.md:22:- Docker alignment documented for v101.1 with HueyOS runtime expectations (`huey-api`, non-root `hueyos`, repository package install) instead of PyGPT as primary runtime.
README.md:75:| **PyGPT-net** | Aperture candidate / later lab interface | Deferred for V1; useful later when richer access/debugging is needed |
README.md:165:**PyGPT-net** is a later aperture candidate and debugging/interface surface. It is not required for V1.
README.md:197:| **PyGPT-net** | Deferred until the system needs richer interface/debug access |
README.md:529:| PyGPT-net | Too heavy and unnecessary for V1 proof |
README.md:733:## PyGPT-net posture
README.md:735:PyGPT-net is useful, but it is not required for V1.
README.md:744:PyGPT-net becomes useful later when the project needs richer interface access, debugging surfaces, and visibility into many agents or modules.
README.md:906:| PyGPT-net | Too heavy for V1; useful later for richer aperture/debugging |
README.md:1128:| **PyGPT-net** | Later aperture/interface candidate; deferred from V1. |
README.md:1202:- PyGPT-net or equivalent aperture/debugging surface,
audit-requirements.txt:108:pygpt-net==2.7.12
constraints.txt:33:pygpt-net==2.7.12
docs/_build/html/_sources/audits/v101.1-repo-control-paths.md.txt:14:- `integrations/pygpt` does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.
docs/_build/html/_sources/security/security-hardening-status.md.txt:150:- `config/pygpt_net/config.json`
docs/_build/html/audits/v101.1-repo-control-paths.html:50:<li><p><code class="docutils literal notranslate"><span class="pre">integrations/pygpt</span></code> does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.</p></li>
docs/_build/html/searchindex.js:1:Search.setIndex({"alltitles":{"1) pip-audit (Python dependency vulnerabilities)":[[3,"pip-audit-python-dependency-vulnerabilities"]],"2) Bandit (Python static security linting)":[[3,"bandit-python-static-security-linting"]],"3) Secret scanning":[[3,"secret-scanning"]],"Compatibility-path decision":[[0,"compatibility-path-decision"]],"Core Docs":[[2,null]],"Docker image pinning policy":[[3,"docker-image-pinning-policy"]],"Environment-specific guidance":[[3,"environment-specific-guidance"]],"Local security checks":[[3,"local-security-checks"]],"Monkey-Head-Project Documentation":[[2,null]],"Providing development secrets safely":[[3,"providing-development-secrets-safely"]],"Resolved hardening items":[[3,"resolved-hardening-items"]],"Runtime impact":[[0,"runtime-impact"]],"Scope and intent":[[3,"scope-and-intent"]],"Security Hardening Status":[[3,null]],"Status disclaimer":[[3,"status-disclaimer"]],"Summary of metadata-only changes":[[0,"summary-of-metadata-only-changes"]],"Token requirements by environment":[[3,"token-requirements-by-environment"]],"Unresolved or manual hardening items":[[3,"unresolved-or-manual-hardening-items"]],"VNC/noVNC safe access pattern":[[3,"vnc-novnc-safe-access-pattern"]],"v101.1 Namespace Migration Direction":[[1,null]],"v101.1 repo-control path cleanup":[[0,null]],"\u201cDo not commit\u201d list":[[3,"do-not-commit-list"]]},"docnames":["audits/v101.1-repo-control-paths","development/v101.1-namespace-migration","index","security/security-hardening-status"],"envversion":{"sphinx":65,"sphinx.domains.c":3,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":9,"sphinx.domains.index":1,"sphinx.domains.javascript":3,"sphinx.domains.math":2,"sphinx.domains.python":4,"sphinx.domains.rst":2,"sphinx.domains.std":2},"filenames":["audits\\v101.1-repo-control-paths.md","development\\v101.1-namespace-migration.md","index.rst","security\\security-hardening-status.md"],"indexentries":{},"objects":{},"objnames":{},"objtypes":{},"terms":{"03":3,"05":[0,3],"1":2,"11":0,"2026":[0,3],"A":3,"If":3,"It":3,"No":[0,1,3],"The":3,"These":3,"accept":3,"access":2,"accident":3,"action":3,"activ":[0,3],"ad":3,"add":1,"addit":3,"address":3,"adjac":3,"affect":3,"again":3,"against":3,"align":3,"alon":3,"alreadi":0,"altern":3,"an":3,"ani":3,"anomali":3,"api":[0,1,3],"app":3,"appli":3,"appropri":3,"approv":3,"ar":3,"artifact":3,"attempt":3,"auth":3,"authent":3,"avoid":3,"back":3,"base":3,"baselin":3,"bastion":3,"bearer":3,"becaus":0,"befor":3,"behavior":1,"block":3,"bootstrap":3,"bound":3,"break":3,"build":3,"cadenc":3,"canon":1,"capabl":3,"central":3,"chang":[1,2,3],"check":2,"ci":3,"cleanup":2,"cli":1,"code":[0,1,3],"codeown":0,"commit":2,"compat":[1,2],"complet":3,"compromis":3,"config":3,"confirm":[0,3],"connect":3,"consid":3,"consist":3,"contain":3,"context":3,"continu":3,"control":[2,3],"core":1,"coverag":3,"credenti":3,"critic":3,"current":3,"cve":3,"cycl":3,"data":3,"date":0,"debug":3,"decis":2,"declar":3,"dedic":3,"defens":3,"deploy":3,"depth":3,"detect":3,"dev":3,"develop":2,"differ":3,"digest":3,"direct":2,"directli":3,"directori":0,"disabl":3,"disclaim":2,"dist":3,"distribut":1,"do":2,"doc":3,"docker":2,"dockerfil":3,"document":[0,1,3],"doe":[0,1,3],"dump":3,"dure":1,"each":3,"empti":1,"enforc":3,"env":3,"environ":2,"ephemer":3,"equival":3,"establish":1,"everi":3,"evolv":3,"exampl":3,"except":3,"exclud":3,"exist":[0,1,3],"expect":3,"expir":3,"explicit":3,"explicitli":1,"export":3,"expos":3,"exposur":3,"featur":3,"file":[0,3],"firewal":3,"float":3,"follow":3,"format":3,"from":[0,3],"front":3,"full":3,"gate":3,"gatewai":3,"gener":3,"gitattribut":0,"github":0,"gitignor":3,"gitleak":3,"gitmodul":0,"glass":3,"gpt":0,"group":3,"guardrail":3,"gui":3,"guidanc":2,"ha":1,"handl":3,"hard":3,"harden":2,"high":3,"higher":3,"histori":3,"hoc":3,"hook":3,"hsm":3,"huei":[0,1],"hueyo":[1,2],"i":[0,1,3],"ident":3,"imag":2,"immedi":3,"immut":3,"impact":2,"implement":[1,3],"import":1,"incid":3,"includ":3,"infrastructur":3,"ingress":3,"inject":3,"input":3,"instal":3,"integr":[0,2,3],"intent":2,"internet":3,"introduc":3,"ip":3,"isol":3,"item":2,"json":3,"justifi":3,"keep":3,"kei":3,"keychain":3,"last":3,"layer":3,"layout":3,"leak":3,"leakag":3,"least":3,"legaci":1,"like":3,"linguist":0,"list":2,"live":3,"local":2,"locat":0,"lockfil":3,"log":3,"long":3,"lowest":3,"m":3,"maintain":[1,3],"mainten":3,"manag":3,"mandatori":3,"manual":2,"match":[0,3],"mean":3,"memori":1,"merg":3,"metadata":[2,3],"mfa":3,"migrat":2,"minim":3,"mirror":3,"moder":3,"modul":1,"monitor":3,"move":1,"must":3,"namespac":2,"nano":0,"need":3,"network":3,"never":3,"new":3,"non":3,"note":3,"novnc":2,"one":3,"ongo":3,"onli":[2,3],"open":3,"oper":3,"out":3,"output":3,"ownership":0,"packag":1,"password":3,"patch":3,"path":[2,3],"pattern":2,"period":3,"perman":3,"pick":3,"pin":2,"placehold":3,"plaintext":3,"plane":3,"point":0,"polici":2,"port":3,"possibl":3,"postur":3,"pr":3,"practic":3,"pre":3,"prefer":3,"present":3,"preserv":1,"privat":3,"privileg":3,"prod":3,"product":3,"prohibit":3,"project":3,"proven":3,"provid":2,"public":3,"purpos":3,"py":[0,1],"pygpt":0,"pygpt_net":3,"pyhuei":[0,2],"python":0,"r":3,"rather":3,"re":3,"real":[0,3],"reassess":3,"rebuild":3,"recommend":3,"record":[1,3],"recur":3,"refer":3,"registri":3,"regular":3,"relat":3,"releas":3,"relev":3,"remain":[1,3],"remedi":3,"remot":3,"remov":[0,3],"repo":[2,3],"report":3,"repositori":[0,3],"resolv":2,"respons":3,"restrict":3,"retain":0,"review":3,"revisit":3,"revoc":3,"revok":3,"risk":3,"rotat":3,"rule":[0,3],"run":3,"runtim":[1,2,3],"safe":2,"sampl":3,"scaffold":1,"scanner":3,"schedul":3,"scope":[1,2],"screenshot":3,"secret":2,"secur":2,"sensit":3,"serv":3,"servic":3,"session":3,"share":3,"shell":3,"short":3,"should":3,"site":2,"so":0,"sourc":[0,3],"specif":2,"src":[0,1],"sso":3,"stage":3,"stale":0,"statu":2,"still":3,"strategi":3,"strict":3,"strong":3,"structur":3,"style":3,"subject":3,"submodul":0,"summari":2,"support":3,"surfac":[1,3],"tag":3,"task":[1,3],"templat":3,"temporari":3,"termin":3,"test":3,"than":3,"thei":3,"thi":[0,1,2,3],"threat":3,"time":[0,3],"tl":3,"toler":3,"track":3,"trail":3,"treat":3,"troubleshoot":3,"trust":3,"tune":3,"under":[1,3],"unless":3,"unresolv":2,"until":1,"up":3,"updat":[0,3],"upgrad":3,"upstream":3,"us":3,"user":3,"v101":2,"valid":3,"valu":3,"var":3,"variabl":3,"vendor":0,"venv":3,"verbos":3,"verif":3,"verifi":3,"version":3,"via":3,"vnc":2,"vpn":3,"wa":0,"were":0,"when":3,"whenev":3,"where":3,"while":3,"window":3,"work":[2,3],"workflow":3,"workload":3,"x":3,"you":3,"zero":3},"titles":["v101.1 repo-control path cleanup","v101.1 Namespace Migration Direction","Monkey-Head-Project Documentation","Security Hardening Status"],"titleterms":{"1":[0,1,3],"2":3,"3":3,"access":3,"audit":3,"bandit":3,"chang":0,"check":3,"cleanup":0,"commit":3,"compat":0,"control":0,"core":2,"decis":0,"depend":3,"develop":3,"direct":1,"disclaim":3,"do":3,"doc":2,"docker":3,"document":2,"environ":3,"guidanc":3,"harden":3,"head":2,"imag":3,"impact":0,"intent":3,"item":3,"lint":3,"list":3,"local":3,"manual":3,"metadata":0,"migrat":1,"monkei":2,"namespac":1,"novnc":3,"onli":0,"path":0,"pattern":3,"pin":3,"pip":3,"polici":3,"project":2,"provid":3,"python":3,"repo":0,"requir":3,"resolv":3,"runtim":0,"safe":3,"scan":3,"scope":3,"secret":3,"secur":3,"specif":3,"static":3,"statu":3,"summari":0,"token":3,"unresolv":3,"v101":[0,1],"vnc":3,"vulner":3}})
docs/_build/html/security/security-hardening-status.html:221:<li><p><code class="docutils literal notranslate"><span class="pre">config/pygpt_net/config.json</span></code></p></li>
docs/audits/v101.1-dependency-source-of-truth.md:54:**Authoritative source: `pyproject.toml` for HueyOS runtime images; `pygpt-net` pin path for optional PyHuey cockpit image**
docs/audits/v101.1-dependency-source-of-truth.md:59:- `infra/docker/pyhuey/Dockerfile` intentionally installs `pygpt-net` directly for optional cockpit/provenance compatibility.
docs/audits/v101.1-dependency-source-of-truth.md:89:   - Docker optional PyHuey cockpit image: explicit `pygpt-net` install (separate intent).
docs/audits/v101.1-docker-alignment.md:4:Align the main HueyOS Docker runtime with the repository package (`hueyos`) and remove PyGPT as the primary runtime.
docs/audits/v101.1-docker-alignment.md:55:- Runtime entrypoint is `huey-api` (HueyOS API), not `pygpt`.
docs/audits/v101.1-pyhuey-branding-string-audit.md:8:- `rg -n "PyGPT|pygpt" src/huey/memory/PY src/hueyos/cli/commands/runtime.py README.md`
docs/audits/v101.1-pyhuey-branding-string-audit.md:10:## Classification of remaining `PyGPT` / `pygpt` strings
docs/audits/v101.1-pyhuey-branding-string-audit.md:14:- `README.md` references to **PyGPT-net** in architecture posture sections as lineage/deferred aperture context.
docs/audits/v101.1-pyhuey-branding-string-audit.md:15:- `src/huey/memory/PY/pygpt_integration.py` docstrings describing PyHuey as forked from PyGPT/PyGPT-net.
docs/audits/v101.1-pyhuey-branding-string-audit.md:19:- `pygpt_net` import/module references across runtime and integration code paths.
docs/audits/v101.1-pyhuey-branding-string-audit.md:20:- `config/pygpt_net/config.json` paths in installer/config helper modules.
docs/audits/v101.1-pyhuey-branding-string-audit.md:21:- CLI version output text: `pygpt_net version: ...` in `src/huey/memory/PY/run.py`.
docs/audits/v101.1-pyhuey-branding-string-audit.md:25:- Additional user-facing references in optional installer scripts and legacy/deferred docs that still print "PyGPT/PyGPT-net" where PyHuey wording may be more appropriate.
docs/audits/v101.1-pyhuey-branding-string-audit.md:26:- Vendored/compatibility tree wording under legacy `pygpt_*` filenames that should be reviewed only when import compatibility is formally migrated.
docs/audits/v101.1-pyhuey-identity-phase1.md:4:Scope: `vendor/pygpt/py-gpt` compatibility stub
docs/audits/v101.1-pyhuey-identity-phase1.md:8:1. Added `pyhuey` console script alias while retaining `pygpt`.
docs/audits/v101.1-pyhuey-identity-phase1.md:9:2. Kept published package metadata name as `pygpt-net` for compatibility.
docs/audits/v101.1-pyhuey-identity-phase1.md:11:4. Added project URLs for Monkey-Head-Project/PyHuey and upstream PyGPT provenance.
docs/audits/v101.1-pyhuey-identity-phase1.md:16:- `pygpt-net` package name remains unchanged in metadata.
docs/audits/v101.1-pyhuey-identity-phase1.md:17:- `pygpt` console script remains available.
docs/audits/v101.1-pyhuey-identity-phase1.md:18:- `pyhuey` points to the same runtime entrypoint as `pygpt`.
docs/audits/v101.1-pyhuey-identity-phase1.md:19:- Upstream PyGPT origin is explicitly cited in README and project URLs.
docs/audits/v101.1-pyhuey-identity-phase1.md:25:- GUI/runtime feature parity with upstream PyGPT.
docs/audits/v101.1-repo-control-paths.md:14:- `integrations/pygpt` does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.
docs/legal/provenance-and-licenses.md:27:- `vendor/pygpt/README.md` states runtime integration order that includes `integrations/pyhuey` and identifies `vendor/pygpt` as static mirrors.
docs/legal/provenance-and-licenses.md:32:## 4) Upstream PyGPT provenance
docs/legal/provenance-and-licenses.md:34:Repository docs already describe PyHuey as derived from upstream PyGPT/PyGPT-net:
docs/legal/provenance-and-licenses.md:36:- `infra/docker/pyhuey/README.md` explicitly says the cockpit image is derived from upstream `pygpt-net` for provenance/compatibility.
docs/legal/provenance-and-licenses.md:37:- `vendor/pygpt/README.md` labels the vendored content as PyGPT/PyGPT-net mirrors.
docs/legal/provenance-and-licenses.md:45:1. **Do not copy code** between Monkey-Head-Project core paths and PyHuey/PyGPT-derived paths without preserving original copyright and license notices.
docs/legal/provenance-and-licenses.md:47:3. **Keep integration paths explicit** (`integrations/pyhuey`, `vendor/pygpt`) so reviewers can distinguish first-party code from fork/vendor code.
docs/security/api-secret-handling.md:13:4. **Local fallback file** `config/pygpt_net/config.json` only when necessary.
docs/security/api-secret-handling.md:17:- Treat `config/pygpt_net/config.json` as **local-only**.
docs/security/security-hardening-status.md:150:- `config/pygpt_net/config.json`
docs/security/tool_permission_boundaries.md:3:This note documents execution boundaries for `huey.pygpt_net.tools.manager.MonkeyManager`.
docs/unsorted/CONTRIBUTING.md:203:- Development: `integrations/pyhuey` tracks the full PyHuey source; `vendor/pygpt/pygpt-mhp` holds the lightweight mirror.
docs/unsorted/repository-restructure-inventory.md:30:- `repo/pygpt-MHP/` + `repo/py-gpt/` ΓåÆ `vendor/pygpt/`
docs/unsorted/repository-restructure-inventory.md:40:- `repo/py-gpt` and `repo/pygpt-MHP` should be consolidated under a single naming scheme (`vendor/pygpt/`).
docs/unsorted/repository-restructure-inventory.md:42:- `src/huey/pygpt_net` naming should be aligned with integration folder naming (`pygpt_net` vs `pygpt`).
docs/unsorted/repository-restructure-recommendation.md:34:ΓööΓöÇΓöÇ vendor/                  # vendored third-party dependencies and PyGPT mirrors
infra/docker/Dockerfile.vnc:1:FROM pygpt:local
infra/docker/Dockerfile.vnc:16:RUN cat > /usr/local/bin/start-vnc-pygpt.sh <<'EOF'
infra/docker/Dockerfile.vnc:56:# Launch PyGPT
infra/docker/Dockerfile.vnc:57:exec pygpt --workdir=/data
infra/docker/Dockerfile.vnc:60:RUN chmod +x /usr/local/bin/start-vnc-pygpt.sh
infra/docker/Dockerfile.vnc:62:# Run as the non-root user that exists in pygpt:local
infra/docker/Dockerfile.vnc:63:USER pygpt
infra/docker/Dockerfile.vnc:64:WORKDIR /home/pygpt
infra/docker/Dockerfile.vnc:67:CMD ["/usr/local/bin/start-vnc-pygpt.sh"]
infra/docker/docker/pygpt/Dockerfile:16:RUN useradd -m -u 1000 pygpt
infra/docker/docker/pygpt/Dockerfile:17:USER pygpt
infra/docker/docker/pygpt/Dockerfile:18:ENV HOME=/home/pygpt \
infra/docker/docker/pygpt/Dockerfile:21:# Install PyGPT from PyPI
infra/docker/docker/pygpt/Dockerfile:23: && pip install --no-cache-dir pygpt-net
infra/docker/docker/pygpt/Dockerfile:25:# PyGPT stores config/data in its workdir; we'll default to /data
infra/docker/docker/pygpt/Dockerfile:26:ENTRYPOINT ["pygpt"]
infra/docker/pyhuey/Dockerfile:3:# Optional PyHuey cockpit/tooling image derived from upstream PyGPT runtime.
infra/docker/pyhuey/Dockerfile:23: && pip install --no-cache-dir pygpt-net
infra/docker/pyhuey/Dockerfile:29:ENTRYPOINT ["pygpt"]
infra/docker/pyhuey/README.md:10:  upstream `pygpt-net` for provenance and compatibility).
infra/docker/pyhuey/README.md:17:PyHuey cockpit packaging here preserves upstream PyGPT provenance by installing
infra/docker/pyhuey/README.md:18:`pygpt-net` and retaining the upstream `pygpt` entrypoint for compatibility.
master-plan-v101.1.json:6:  "description": "Master Plan V101.1: PyHuey cockpit alignment release. V101.1 preserves the V101.0 Legion Go / Huey Brain V1 scope lock while adding PyHuey as the project-controlled fork of PyGPT and the Windows 11 Pro cockpit/build/runtime surface for Huey. It standardizes repository paths around integrations/pyhuey and platform/windows/huey, records Python 3.13 as the Windows Huey/PyHuey target branch, keeps Windows/PyHuey out of Huey Brain sovereignty, and treats docs, website, GitHub/README, and the master plan as the human-readable build-record surfaces.",
master-plan-v101.1.json:82:    "pygpt_net_role",
master-plan-v101.1.json:128:      "Atlas should prevent V1 from drifting into Huey Body actuation, live microphone work, enclosure modification, distributed compute, HIMS runtime, PyGPT-net, or full governance implementation.",
master-plan-v101.1.json:143:      "Do not reactivate PyGPT-net, HIMS, multi-agent governance, or Huey Body actuation inside V1 unless Dylan explicitly reopens scope.",
master-plan-v101.1.json:310:      "PyGPT-net or richer aperture after CLI/queue proof stabilizes.",
master-plan-v101.1.json:347:      "PyHuey": "Windows 11 Pro cockpit/build/runtime tooling forked from PyGPT; active as LabTech/cockpit integration surface, not the V1 proof runtime."
master-plan-v101.1.json:364:      "PyGPT_net": "Later aperture/debugging surface, not V1.",
master-plan-v101.1.json:396:      "Keep Huey Body, live microphone, wake word, PyGPT-net, HIMS runtime, governance runtime, and distributed compute out of V1."
master-plan-v101.1.json:408:    "conflict_policy": "If older docs describe Huey Core as the current proof body, place cognition on the Body, activate PyGPT-net/HIMS/governance in V1, or distribute V1 compute, preserve them as history and implement V101.0 unless Dylan explicitly reopens scope.",
master-plan-v101.1.json:427:        "PyHuey is the project-controlled fork of PyGPT and the Windows 11 Pro cockpit for Huey.",
master-plan-v101.1.json:444:      "integrations/pyhuey": "Source fork of PyGPT renamed PyHuey for project-facing cockpit work.",
master-plan-v101.1.json:445:      "integrations/pygpt": "Allowed short-term alias only if tooling expects the upstream name; not the preferred V101.1 path.",
master-plan-v101.1.json:477:      "PyGPT-net": "Deferred aperture / diagnostic interface candidate; not V1 infrastructure.",
master-plan-v101.1.json:480:      "PyHuey": "Project-controlled fork of PyGPT; Windows 11 Pro cockpit, integration-test surface, and build/runtime tooling for Huey. Active as cockpit/tooling, not Huey Brain sovereignty or V1 proof runtime.",
master-plan-v101.1.json:481:      "PyGPT / PyGPT-net": "Upstream/source-lineage name and historical aperture wording. The active project-facing fork name is PyHuey."
master-plan-v101.1.json:489:      "Use PyHuey as the project-facing name for the forked PyGPT cockpit.",
master-plan-v101.1.json:490:      "Use integrations/pyhuey as the preferred source fork path; integrations/pygpt is only a compatibility alias.",
master-plan-v101.1.json:515:      "PyGPT-net as primary aperture",
master-plan-v101.1.json:595:    "pygpt_net": {
master-plan-v101.1.json:601:      "role": "project-controlled PyGPT fork and Windows 11 Pro cockpit for Huey",
master-plan-v101.1.json:603:      "responsibility": "provide controlled Windows cockpit, provider/tool testing, PyGPT-derived interface work, Redis/vector-store patch experimentation, launch/build scripts, and reproducible Python 3.13 freezes.",
master-plan-v101.1.json:662:      "python": "Python 3.13.x target branch; current proof used Python 3.13.13 in Venvs/PyGPT.",
master-plan-v101.1.json:665:      "venv_policy": "Project venv may remain Venvs/PyGPT locally during transition, but repository-facing name is PyHuey.",
master-plan-v101.1.json:885:      "PyGPT-net GUI or aperture layer",
master-plan-v101.1.json:1029:  "pygpt_net_role": {
master-plan-v101.1.json:1030:    "name": "PyGPT / PyGPT-net",
master-plan-v101.1.json:1033:    "v101_1_decision": "Fork PyGPT as PyHuey. Use PyHuey for the project cockpit and controlled Windows 11 Pro Python 3.13 branch. Keep PyGPT/PyGPT-net as upstream/source-lineage terminology.",
master-plan-v101.1.json:1770:      "logical_session_path": "Portal terminal -> SSH transport -> Huey-side portal bridge -> PyGPT-net aperture -> HIMS -> internal deliberation or execution path"
master-plan-v101.1.json:1792:      "huey_side": "Huey computation, memory, PyGPT-net, HIMS, and governance continue to live on the Debian / HueyOS side.",
master-plan-v101.1.json:2129:        "PyGPT-net or HIMS is introduced to replace the simple pipeline.",
master-plan-v101.1.json:2158:      "future": "live mic, body actuation, HIMS, PyGPT-net, and governance are reintroduced only after V1 is stable."
master-plan-v101.1.json:2176:    "Clarify the future role of PyGPT-net once the Legion Go pipeline succeeds.",
master-plan-v101.1.json:2325:      "Moved PyGPT-net out of V1 and into deferred aperture/debugging status.",
master-plan-v101.1.json:2369:      "Added Windows stack policy: Windows 10/11, WSL, and PyGPT are LabTech/cockpit/fallback layers, not Huey sovereignty.",
master-plan-v101.1.json:2391:    "Do not reintroduce PyGPT-net, HIMS, live mic, body actuation, or governance runtime until the Legion Go loop is proven.",
master-plan-v101.1.json:2400:    "Windows 10/11, WSL, and PyGPT are LabTech/cockpit/fallback layers, not Huey sovereignty.",
master-plan-v101.1.json:2472:      "Kept Huey Body, HIMS runtime, PyGPT-net, live microphone input, governance runtime, and Farm compute deferred."
master-plan-v101.1.json:2488:      "Preserved the V100.9 scope lock: stock Legion Go, controlled MP3 fixtures, faster-whisper, API bridge, structured logging, no Body/HIMS/PyGPT-net/governance/live mic/distributed compute in V1."
master-plan-v101.1.json:2521:        "PyGPT-net",
master-plan-v101.1.json:2591:      "PyHuey": "forked PyGPT cockpit, Python 3.13 Windows branch, controlled update cycle",
master-plan-v101.1.json:2606:      "integrations/pyhuey": "source fork of PyGPT; preferred V101.1 path",
master-plan-v101.1.json:2607:      "integrations/pygpt": "temporary compatibility alias only if needed",
master-plan-v101.1.json:2659:      "decision": "Windows 10/11, WSL, and PyGPT work are LabTech/cockpit/fallback layers.",
master-plan-v101.1.json:2660:      "rule": "Do not let Windows, WSL, or PyGPT become Huey sovereignty by implication."
master-plan-v101.1.json:2690:    "basis": "Fork of PyGPT / PyGPT-net for project-controlled cockpit work.",
master-plan-v101.1.json:2693:    "temporary_alias": "integrations/pygpt only if needed by tooling or transition scripts",
master-plan-v101.1.json:2705:      "baseline": "Python 3.13 PyGPT/PyHuey venv reached pip check clean and passed core import tests.",
master-plan-v101.1.json:2714:    "update_policy": "Control the update cycle through the PyHuey fork. Upstream PyGPT changes should be pulled deliberately, tested against the Windows 11 Pro/Python 3.13 branch, and tagged before promotion."
master-plan-v101.1.json:2717:    "integrations/pyhuey": "PyHuey source fork of PyGPT, controlled by the project.",
master-plan-v101.1.json:2725:    "Fork PyGPT as PyHuey.",
master-plan-v101.1.json:2727:    "Use integrations/pyhuey as the preferred source fork path; integrations/pygpt is a temporary compatibility alias only.",
platform/installers/debian/Debian/install-deb.sh:21:CONFIG_DIR="$INSTALL_DIR/config/pygpt_net"
platform/installers/debian/Debian/install-deb.sh:264:    echo "Installing audio runtime packages for PyGPT/PyGPT-net ..."
platform/installers/debian/Debian/install-deb.sh:382:    echo "Installing PyGPT-net and audio Python dependencies ..."
platform/installers/debian/Debian/install-deb.sh:383:    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile
platform/installers/debian/Debian/install-deb.sh:385:    local submodule_path="$PROJECT_ROOT/vendor/pygpt/pygpt-mhp"
platform/installers/debian/Debian/install-deb.sh:387:        echo "Installing local pygpt-MHP integration in editable mode ..."
platform/installers/debian/Debian/install-deb.sh:394:    echo "Synchronising pygpt structure ..."
platform/installers/debian/Debian/install-deb.sh:395:    "$python_bin" "$PROJECT_ROOT/huey/memory/PY/sync_pygpt_structure.py" || \
platform/installers/debian/Debian/install-deb.sh:396:        echo "Warning: sync_pygpt_structure.py failed"
platform/installers/debian/Debian/install-deb.sh:452:config_path = Path(os.environ.get("HUEYOS_CONFIG_FILE", "/opt/hueyos/config/pygpt_net/config.json"))
platform/installers/debian/Debian/update-deb.sh:192:    echo "Ensuring audio runtime packages for PyGPT/PyGPT-net are installed ..."
platform/installers/debian/Debian/update-deb.sh:277:    echo "Updating PyGPT-net and audio Python dependencies ..."
platform/installers/debian/Debian/update-deb.sh:278:    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile
platform/installers/debian/Debian/update-deb.sh:280:    local submodule_path="$project_root/vendor/pygpt/pygpt-mhp"
platform/installers/debian/Debian/update-deb.sh:282:        echo "Reinstalling local pygpt-MHP integration in editable mode ..."
platform/installers/debian/Debian/update-deb.sh:316:    if [[ -f "$project_root/huey/memory/PY/sync_pygpt_structure.py" ]]; then
platform/installers/debian/Debian/update-deb.sh:317:        echo "Synchronising pygpt structure ..."
platform/installers/debian/Debian/update-deb.sh:318:        "$py_bin" "$project_root/huey/memory/PY/sync_pygpt_structure.py" || \
platform/installers/debian/Debian/update-deb.sh:319:            echo "Warning: sync_pygpt_structure.py failed" >&2
platform/installers/macos/macOS/install-mac.sh:399:  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
platform/installers/macos/macOS/install-mac.sh:400:    log "Installing local package: vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/install-mac.sh:401:    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/install-mac.sh:403:    warn "Local package vendor/pygpt/pygpt-mhp not found (skipping editable install)."
platform/installers/macos/macOS/install-mac.sh:408:  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
platform/installers/macos/macOS/install-mac.sh:410:    python "$INSTALL_DIR/sync_pygpt_structure.py"
platform/installers/macos/macOS/install-mac.sh:412:    [[ "$VERBOSE" -eq 1 ]] && warn "sync_pygpt_structure.py not found (skipping)."
platform/installers/macos/macOS/update-mac.sh:367:  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
platform/installers/macos/macOS/update-mac.sh:368:    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/update-mac.sh:370:    [[ "$VERBOSE" -eq 1 ]] && warn "Local package vendor/pygpt/pygpt-mhp not found (skipping)."
platform/installers/macos/macOS/update-mac.sh:375:  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
platform/installers/macos/macOS/update-mac.sh:377:    python "$INSTALL_DIR/sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.bat:167:REM Logic from 01-FULL.bat: setupPythonEnv + sync_pygpt_structure.py + connectivity check
platform/installers/windows/Windows/install-win.bat:408:if exist "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp" (
platform/installers/windows/Windows/install-win.bat:409:    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/install-win.bat:410:    call :checkError "Install pygpt-MHP"
platform/installers/windows/Windows/install-win.bat:412:    echo [INFO] vendor\pygpt\pygpt-mhp not found; skipping editable install.
platform/installers/windows/Windows/install-win.bat:415:if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
platform/installers/windows/Windows/install-win.bat:416:    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.ps1:486:  # Install vendored pygpt-MHP package (if present)
platform/installers/windows/Windows/install-win.ps1:487:  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/install-win.ps1:488:  if (Test-Path -LiteralPath $pygptPath) {
platform/installers/windows/Windows/install-win.ps1:489:    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir
platform/installers/windows/Windows/install-win.ps1:491:    Write-Log "Vendor path not found (vendor\pygpt\pygpt-mhp). Skipping editable install." 'WARN'
platform/installers/windows/Windows/install-win.ps1:495:  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.ps1:499:    Write-Log "sync_pygpt_structure.py not found; skipping." 'WARN'
platform/installers/windows/Windows/update-win.bat:292:if exist "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp" (
platform/installers/windows/Windows/update-win.bat:293:    echo Installing pygpt-MHP editable...
platform/installers/windows/Windows/update-win.bat:294:    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/update-win.bat:295:    call :checkError "Install pygpt-MHP"
platform/installers/windows/Windows/update-win.bat:298:if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
platform/installers/windows/Windows/update-win.bat:299:    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
platform/installers/windows/Windows/update-win.ps1:391:  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/update-win.ps1:392:  if (Test-Path -LiteralPath $pygptPath) {
platform/installers/windows/Windows/update-win.ps1:393:    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir -AllowNonZero
platform/installers/windows/Windows/update-win.ps1:396:  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
pyproject.toml:116:  "pygpt-net==2.7.12",
requirements.txt:109:pygpt-net==2.7.12
scripts/check_canon_terms.py:117:def _should_flag_pygpt(line: str) -> bool:
scripts/check_canon_terms.py:118:    if not re.search(r"\\bPyGPT\\b", line):
scripts/check_canon_terms.py:141:            if _should_flag_pygpt(line):
scripts/check_canon_terms.py:143:                    f"{path}:{lineno}: Use PyHuey as the active cockpit name; keep PyGPT for provenance only."
scripts/check_repo_drift.py:74:        name="docker-primary-pygpt",
scripts/check_repo_drift.py:75:        pattern=re.compile(r"\b(pygpt|pygpt-net)\b", re.IGNORECASE),
scripts/check_repo_drift.py:76:        message="Do not present PyGPT as the primary runtime in main Dockerfiles; use hueyos/HueyOS runtime entrypoints.",
scripts/check_repo_drift.py:137:    if rule.name == "docker-primary-pygpt":
scripts/check_repo_drift.py:157:                name="integrations-pygpt-path",
scripts/check_repo_drift.py:158:                pattern=re.compile(r"\bintegrations/pygpt\b"),
src/huey/__init__.py:21:    "pygpt_integration",
src/huey/memory/BAT/01-FULL.bat:150:pip install -e vendor\pygpt\pygpt-mhp
src/huey/memory/BAT/01-FULL.bat:151:call :checkError "Install pygpt-MHP"
src/huey/memory/BAT/01-FULL.bat:152:python sync_pygpt_structure.py
src/huey/memory/BAT/build.bat:14:Placeholder for `repo/pygpt-MHP/bin/build.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_all.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_all.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_installer.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_installer.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/pygpt-launch-&-update.bat:4:REM HueyOS: Pygpt Launch & Update batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-launch-&-update.bat:14:python -m pip install --upgrade pygpt-MHP
src/huey/memory/BAT/pygpt-launch-&-update.bat:15:pygpt
src/huey/memory/BAT/pygpt-launch.bat:4:REM HueyOS: Pygpt Launch batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-launch.bat:14:pygpt
src/huey/memory/BAT/pygpt-update.bat:4:REM HueyOS: Pygpt Update batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-update.bat:14:python -m pip install --upgrade pygpt-MHP
src/huey/memory/DOCKER/Dockerfile:31:# Install PyGPT
src/huey/memory/DOCKER/Dockerfile:33: && pip install --no-cache-dir pygpt-net
src/huey/memory/DOCKER/Dockerfile:36:RUN useradd -m -u 1000 pygpt \
src/huey/memory/DOCKER/Dockerfile:38: && chown -R pygpt:pygpt /data
src/huey/memory/DOCKER/Dockerfile:40:USER pygpt
src/huey/memory/DOCKER/Dockerfile:41:WORKDIR /home/pygpt
src/huey/memory/DOCKER/Dockerfile:46:ENTRYPOINT ["pygpt"]
src/huey/memory/DOCKER/Dockerfile.vnc:1:FROM pygpt:local
src/huey/memory/DOCKER/Dockerfile.vnc:20:# - Runs PyGPT as non-root user "pygpt"
src/huey/memory/DOCKER/Dockerfile.vnc:21:RUN cat > /usr/local/bin/start-vnc-pygpt.sh <<'EOF'
src/huey/memory/DOCKER/Dockerfile.vnc:67:  echo "[start-vnc-pygpt] Generated VNC password: ${VNC_PASSWORD}"
src/huey/memory/DOCKER/Dockerfile.vnc:80:# Run PyGPT as non-root
src/huey/memory/DOCKER/Dockerfile.vnc:81:exec pygpt --workdir=/data
src/huey/memory/DOCKER/Dockerfile.vnc:85:RUN sed -i 's/\r$//' /usr/local/bin/start-vnc-pygpt.sh \
src/huey/memory/DOCKER/Dockerfile.vnc:86: && chmod +x /usr/local/bin/start-vnc-pygpt.sh
src/huey/memory/DOCKER/Dockerfile.vnc:89:USER pygpt
src/huey/memory/DOCKER/Dockerfile.vnc:90:ENTRYPOINT ["/usr/local/bin/start-vnc-pygpt.sh"]
src/huey/memory/JSON/PyGPT_Change_Log.json:31:        "Audio output switched from PyGame to PyAudio. It may be necessary to manually connect Alsa in Snap version with: \"sudo snap connect pygpt:alsa\".",
src/huey/memory/JSON/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
src/huey/memory/JSON/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
src/huey/memory/JSON/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
src/huey/memory/MD/duplicate-files.md:19:  - `repo/pygpt-MHP/src/pygpt_net/data/config/settings_section.json`
src/huey/memory/MD/duplicate-files.md:21:  - `src/huey/pygpt_net/data/config/settings_section.json`
src/huey/memory/MD/duplicate-files.md:25:  - `repo/pygpt-MHP/src/pygpt_net/data/config/settings.json`
src/huey/memory/MD/duplicate-files.md:27:  - `src/huey/pygpt_net/data/config/settings.json`
src/huey/memory/MD/duplicate-files.md:31:  - `repo/pygpt-MHP/src/pygpt_net/data/config/models.json`
src/huey/memory/MD/duplicate-files.md:33:  - `src/huey/pygpt_net/data/config/models.json`
src/huey/memory/MD/duplicate-files.md:37:  - `repo/pygpt-MHP/src/pygpt_net/data/config/modes.json`
src/huey/memory/MD/duplicate-files.md:39:  - `src/huey/pygpt_net/data/config/modes.json`
src/huey/memory/MD/duplicate-files.md:43:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.research.json`
src/huey/memory/MD/duplicate-files.md:45:  - `src/huey/pygpt_net/data/config/presets/current.research.json`
src/huey/memory/MD/duplicate-files.md:49:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/joke_expert.json`
src/huey/memory/MD/duplicate-files.md:51:  - `src/huey/pygpt_net/data/config/presets/joke_expert.json`
src/huey/memory/MD/duplicate-files.md:55:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.agent_llama.json`
src/huey/memory/MD/duplicate-files.md:57:  - `src/huey/pygpt_net/data/config/presets/current.agent_llama.json`
src/huey/memory/MD/duplicate-files.md:61:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.img.json`
src/huey/memory/MD/duplicate-files.md:63:  - `src/huey/pygpt_net/data/config/presets/current.img.json`
src/huey/memory/MD/duplicate-files.md:67:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.assistant.json`
src/huey/memory/MD/duplicate-files.md:69:  - `src/huey/pygpt_net/data/config/presets/current.assistant.json`
src/huey/memory/MD/duplicate-files.md:73:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.chat.json`
src/huey/memory/MD/duplicate-files.md:75:  - `src/huey/pygpt_net/data/config/presets/current.chat.json`
src/huey/memory/MD/duplicate-files.md:79:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_react.json`
src/huey/memory/MD/duplicate-files.md:81:  - `src/huey/pygpt_net/data/config/presets/agent_react.json`
src/huey/memory/MD/duplicate-files.md:85:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/batman_and_joker.json`
src/huey/memory/MD/duplicate-files.md:87:  - `src/huey/pygpt_net/data/config/presets/batman_and_joker.json`
src/huey/memory/MD/duplicate-files.md:91:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/dalle_white_cat.json`
src/huey/memory/MD/duplicate-files.md:93:  - `src/huey/pygpt_net/data/config/presets/dalle_white_cat.json`
src/huey/memory/MD/duplicate-files.md:97:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_planner.json`
src/huey/memory/MD/duplicate-files.md:99:  - `src/huey/pygpt_net/data/config/presets/agent_planner.json`
src/huey/memory/MD/duplicate-files.md:103:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.completion.json`
src/huey/memory/MD/duplicate-files.md:105:  - `src/huey/pygpt_net/data/config/presets/current.completion.json`
src/huey/memory/MD/duplicate-files.md:109:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.llama_index.json`
src/huey/memory/MD/duplicate-files.md:111:  - `src/huey/pygpt_net/data/config/presets/current.llama_index.json`
src/huey/memory/MD/duplicate-files.md:115:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.vision.json`
src/huey/memory/MD/duplicate-files.md:117:  - `src/huey/pygpt_net/data/config/presets/current.vision.json`
src/huey/memory/MD/duplicate-files.md:121:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.audio.json`
src/huey/memory/MD/duplicate-files.md:123:  - `src/huey/pygpt_net/data/config/presets/current.audio.json`
src/huey/memory/MD/duplicate-files.md:127:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.expert.json`
src/huey/memory/MD/duplicate-files.md:129:  - `src/huey/pygpt_net/data/config/presets/current.expert.json`
src/huey/memory/MD/duplicate-files.md:133:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/joke_agent.json`
src/huey/memory/MD/duplicate-files.md:135:  - `src/huey/pygpt_net/data/config/presets/joke_agent.json`
src/huey/memory/MD/duplicate-files.md:139:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.agent.json`
src/huey/memory/MD/duplicate-files.md:141:  - `src/huey/pygpt_net/data/config/presets/current.agent.json`
src/huey/memory/MD/duplicate-files.md:145:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_openai_assistant.json`
src/huey/memory/MD/duplicate-files.md:147:  - `src/huey/pygpt_net/data/config/presets/agent_openai_assistant.json`
src/huey/memory/MD/duplicate-files.md:151:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.langchain.json`
src/huey/memory/MD/duplicate-files.md:153:  - `src/huey/pygpt_net/data/config/presets/current.langchain.json`
src/huey/memory/MD/duplicate-files.md:157:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_openai.json`
src/huey/memory/MD/duplicate-files.md:159:  - `src/huey/pygpt_net/data/config/presets/agent_openai.json`
src/huey/memory/MD/duplicate-files.md:163:  - `repo/pygpt-MHP/src/pygpt_net/data/prompts.csv`
src/huey/memory/MD/duplicate-files.md:164:  - `src/huey/pygpt_net/data/prompts.csv`
src/huey/memory/MD/duplicate-files.md:168:  - `repo/pygpt-MHP/src/pygpt_net/data/config/config.json`
src/huey/memory/MD/duplicate-files.md:169:  - `src/huey/pygpt_net/data/config/config.json`
src/huey/memory/MD/duplicate-files.md:173:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/pirate_captain.json`
src/huey/memory/MD/duplicate-files.md:174:  - `src/huey/pygpt_net/data/config/presets/pirate_captain.json`
src/huey/memory/MD/duplicate-files.md:178:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/wild_west_cowboy.json`
src/huey/memory/MD/duplicate-files.md:179:  - `src/huey/pygpt_net/data/config/presets/wild_west_cowboy.json`
src/huey/memory/MD/duplicate-files.md:183:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/mad_scientist.json`
src/huey/memory/MD/duplicate-files.md:184:  - `src/huey/pygpt_net/data/config/presets/mad_scientist.json`
src/huey/memory/MD/duplicate-files.md:188:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/noir_detective.json`
src/huey/memory/MD/duplicate-files.md:189:  - `src/huey/pygpt_net/data/config/presets/noir_detective.json`
src/huey/memory/MD/duplicate-files.md:193:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/fantasy_bard.json`
src/huey/memory/MD/duplicate-files.md:194:  - `src/huey/pygpt_net/data/config/presets/fantasy_bard.json`
src/huey/memory/MD/placeholder-occurrences.md:9:- `repo/py-gpt/src/pygpt_net/__init__.py`:3 - `This placeholder mirrors the directory layout of the upstream `py-gpt``
src/huey/memory/MD/placeholder-occurrences.md:10:- `repo/pygpt-MHP/src/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:11:- `repo/pygpt-MHP/src/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:12:- `src/huey/memory/CSV/pygpt_prompts.csv`:133 - `Web Browser,"You are a Web Browser. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:24:- `src/huey/memory/PY/sync_pygpt_structure.py`:31 - `"""Return True if ``dst`` does not exist or contains a placeholder header."""`
src/huey/memory/MD/placeholder-occurrences.md:25:- `src/huey/memory/PY/sync_pygpt_structure.py`:50 - `"""Copy file or directory from src to dst if missing or placeholder."""`
src/huey/memory/MD/placeholder-occurrences.md:28:- `src/huey/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:29:- `src/huey/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:31:- `tests/test_placeholder.py`:3 - `from huey.pygpt_net.controller.config.placeholder import Placeholder`
src/huey/memory/PY/ai_processor.py:47:    (LLM) ΓÇô currently ``ollama`` or ``pygpt_net`` ΓÇô for semantic text
src/huey/memory/PY/ai_processor.py:82:            ("pygpt_net", self._init_pygpt_backend),
src/huey/memory/PY/ai_processor.py:126:    def _init_pygpt_backend(self) -> object | None:
src/huey/memory/PY/ai_processor.py:127:        """Return a ``pygpt_net`` client instance when possible."""
src/huey/memory/PY/ai_processor.py:129:        spec = importlib.util.find_spec("pygpt_net")
src/huey/memory/PY/ai_processor.py:133:        module = importlib.import_module("pygpt_net")
src/huey/memory/PY/ai_processor.py:253:        elif self._llm_backend == "pygpt_net":
src/huey/memory/PY/ai_tools_gui.py:153:    config = ConfigManager("config/pygpt_net/config.json")
src/huey/memory/PY/check_inter_program_connectivity.py:15:"""Verify that hueyos and pygpt_net modules import successfully."""
src/huey/memory/PY/check_inter_program_connectivity.py:21:    from .pygpt_integration import prepare_pygpt
src/huey/memory/PY/check_inter_program_connectivity.py:23:    from pygpt_integration import prepare_pygpt  # type: ignore
src/huey/memory/PY/check_inter_program_connectivity.py:33:    return prepare_pygpt()
src/huey/memory/PY/config_toggle_gui.py:32:DEFAULT_CONFIG = "config/pygpt_net/config.json"
src/huey/memory/PY/example_plugin.py:14:"""Minimal example plugin for the PyGPT application."""
src/huey/memory/PY/example_plugin.py:18:from pygpt_net.plugin.base.plugin import BasePlugin
src/huey/memory/PY/example_tool.py:14:"""Tiny custom tool usable with the PyGPT GUI."""
src/huey/memory/PY/example_tool.py:20:from pygpt_net.tools.base import BaseTool
src/huey/memory/PY/install_gui.py:29:DEFAULT_CONFIG_PATH = Path("config") / "pygpt_net" / "config.json"
src/huey/memory/PY/installer.py:158:            [sys.executable, "sync_pygpt_structure.py"],
src/huey/memory/PY/license_cli.py:19:DEFAULT_CONFIG = "config/pygpt_net/config.json"
src/huey/memory/PY/license_gui.py:50:def show_license_gui(config_path: str | Path = "config/pygpt_net/config.json") -> None:
src/huey/memory/PY/llm.py:6:"""Abstractions for interacting with LLM providers via the PyHuey/PyGPT-net stack."""
src/huey/memory/PY/llm.py:15:from huey.pygpt_integration import prepare_pygpt
src/huey/memory/PY/llm.py:41:        self._pygpt_agent: Any | None = None
src/huey/memory/PY/llm.py:42:        self._register_with_pygpt()
src/huey/memory/PY/llm.py:81:        """Load preset metadata from the pygpt configuration tree."""
src/huey/memory/PY/llm.py:83:        if not prepare_pygpt():
src/huey/memory/PY/llm.py:88:            resources.files("pygpt_net") / "data" / "config" / "presets" / preset_name
src/huey/memory/PY/llm.py:96:    def _register_with_pygpt(self) -> None:
src/huey/memory/PY/llm.py:97:        """Instantiate a pygpt agent wrapper for integration metadata."""
src/huey/memory/PY/llm.py:99:        if not prepare_pygpt():
src/huey/memory/PY/llm.py:100:            self._pygpt_agent = None
src/huey/memory/PY/llm.py:105:                from pygpt_net.provider.agents.openai import (
src/huey/memory/PY/llm.py:109:                from pygpt_net.provider.agents.react import ReactAgent as ProviderAgent
src/huey/memory/PY/llm.py:111:                from pygpt_net.provider.agents.planner import (
src/huey/memory/PY/llm.py:115:            self._pygpt_agent = None
src/huey/memory/PY/llm.py:119:            self._pygpt_agent = ProviderAgent()
src/huey/memory/PY/llm.py:121:            self._pygpt_agent = None
src/huey/memory/PY/preload_data.py:15:    prompts_file = BASE_DIR / "prompts" / "pygpt_prompts.csv"
src/huey/memory/PY/pygpt_custom_cli.py:4:# HueyOS: Pygpt Custom Cli module (huey)
src/huey/memory/PY/pygpt_custom_cli.py:13:from .pygpt_memory import Memory
src/huey/memory/PY/pygpt_custom_cli.py:16:class CustomPyGPT:
src/huey/memory/PY/pygpt_custom_cli.py:83:__all__ = ["CustomPyGPT"]
src/huey/memory/PY/pygpt_integration.py:1:"""Utility helpers for wiring PyHuey/PyGPT-net into Monkey Head.
src/huey/memory/PY/pygpt_integration.py:4:of ``pygpt_net``.  They are intentionally lightweight so they can be imported
src/huey/memory/PY/pygpt_integration.py:17:_PYGPT_PREPARED = False
src/huey/memory/PY/pygpt_integration.py:18:_PYGPT_ACTIVE_SOURCE: "PyHueySource | None" = None
src/huey/memory/PY/pygpt_integration.py:23:    """A possible source tree for the ``pygpt_net`` package."""
src/huey/memory/PY/pygpt_integration.py:74:        "pygpt-mhp": "vendor",
src/huey/memory/PY/pygpt_integration.py:86:    """Return ordered PyHuey/PyGPT-net source candidates."""
src/huey/memory/PY/pygpt_integration.py:93:            package_path=root / "src" / "huey" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:95:            description="Lightweight PyGPT-net compatibility package shipped with HueyOS.",
src/huey/memory/PY/pygpt_integration.py:100:            package_path=root / "integrations" / "pyhuey" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:106:            path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src",
src/huey/memory/PY/pygpt_integration.py:107:            package_path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:109:            description="Vendored lightweight pygpt-MHP mirror.",
src/huey/memory/PY/pygpt_integration.py:113:            path=root / "vendor" / "pygpt" / "py-gpt" / "src",
src/huey/memory/PY/pygpt_integration.py:114:            package_path=root / "vendor" / "pygpt" / "py-gpt" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:120:            path=root / "pygpt",
src/huey/memory/PY/pygpt_integration.py:121:            package_path=root / "pygpt" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:123:            description="Historical root-level PyGPT checkout.",
src/huey/memory/PY/pygpt_integration.py:127:            path=root / "pygpt" / "src",
src/huey/memory/PY/pygpt_integration.py:128:            package_path=root / "pygpt" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:130:            description="Historical root-level PyGPT src checkout.",
src/huey/memory/PY/pygpt_integration.py:134:            path=root / "repo" / "pygpt-MHP" / "src",
src/huey/memory/PY/pygpt_integration.py:135:            package_path=root / "repo" / "pygpt-MHP" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:137:            description="Historical repo/pygpt-MHP checkout.",
src/huey/memory/PY/pygpt_integration.py:142:    env_value = os.environ.get("PYGPT_EXTRA_PATHS")
src/huey/memory/PY/pygpt_integration.py:154:                package_path=source_path / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:156:                description="Operator-provided PyGPT-net source path.",
src/huey/memory/PY/pygpt_integration.py:174:    """Return ordered candidate directories that may house ``pygpt_net`` sources."""
src/huey/memory/PY/pygpt_integration.py:182:    """Return source candidates that currently contain ``pygpt_net``."""
src/huey/memory/PY/pygpt_integration.py:203:def prepare_pygpt(
src/huey/memory/PY/pygpt_integration.py:204:    module_name: str = "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:215:    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
src/huey/memory/PY/pygpt_integration.py:218:    if _PYGPT_PREPARED:
src/huey/memory/PY/pygpt_integration.py:222:        _PYGPT_PREPARED = True
src/huey/memory/PY/pygpt_integration.py:223:        _PYGPT_ACTIVE_SOURCE = None
src/huey/memory/PY/pygpt_integration.py:238:            _PYGPT_PREPARED = True
src/huey/memory/PY/pygpt_integration.py:239:            _PYGPT_ACTIVE_SOURCE = candidate
src/huey/memory/PY/pygpt_integration.py:246:    module_name: str = "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:252:    prepared = prepare_pygpt(module_name, source=source)
src/huey/memory/PY/pygpt_integration.py:260:            _PYGPT_ACTIVE_SOURCE.as_dict()
src/huey/memory/PY/pygpt_integration.py:261:            if _PYGPT_ACTIVE_SOURCE
src/huey/memory/PY/pygpt_integration.py:268:def reset_pygpt_state() -> None:
src/huey/memory/PY/pygpt_integration.py:271:    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
src/huey/memory/PY/pygpt_integration.py:272:    _PYGPT_PREPARED = False
src/huey/memory/PY/pygpt_integration.py:273:    _PYGPT_ACTIVE_SOURCE = None
src/huey/memory/PY/pygpt_integration.py:281:    "prepare_pygpt",
src/huey/memory/PY/pygpt_integration.py:284:    "reset_pygpt_state",
src/huey/memory/PY/pygpt_memory.py:4:# HueyOS: Pygpt Memory module (huey)
src/huey/memory/PY/pygpt_memory.py:6:"""Simplified conversation memory helpers for Monkey Head's PyGPT integration."""
src/huey/memory/PY/pygpt_memory.py:12:    """A minimal conversation buffer compatible with the legacy PyGPT tooling."""
src/huey/memory/PY/resources.py:32:        os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "icons"
src/huey/memory/PY/resources.py:35:        os.path.dirname(__file__), "..", "src", "pygpt_net", "icons.qrc"
src/huey/memory/PY/resources.py:45:            "pygpt_net",
src/huey/memory/PY/resources.py:51:            os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "js", "katex"
src/huey/memory/PY/resources.py:55:        os.path.dirname(__file__), "..", "src", "pygpt_net", "js.qrc"
src/huey/memory/PY/resources.py:62:            os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "js", "katex"
src/huey/memory/PY/resources.py:66:        os.path.dirname(__file__), "..", "src", "pygpt_net", "css.qrc"
src/huey/memory/PY/resources.py:76:            "pygpt_net",
src/huey/memory/PY/resources.py:84:        os.path.dirname(__file__), "..", "src", "pygpt_net", "fonts.qrc"
src/huey/memory/PY/run.py:19:from .pygpt_integration import prepare_pygpt, pyhuey_status
src/huey/memory/PY/run.py:26:    from .pygpt_custom_cli import CustomPyGPT
src/huey/memory/PY/run.py:28:    CustomPyGPT().run_cli()
src/huey/memory/PY/run.py:64:def _prepare_pygpt(source: str | None = None) -> bool:
src/huey/memory/PY/run.py:65:    """Ensure :mod:`pygpt_net` is importable either from site-packages or vendors."""
src/huey/memory/PY/run.py:67:    return prepare_pygpt(source=source)
src/huey/memory/PY/run.py:77:    if not _prepare_pygpt(source):
src/huey/memory/PY/run.py:81:        from pygpt_net.app import run as cli_run
src/huey/memory/PY/run.py:97:    if not _prepare_pygpt(source):
src/huey/memory/PY/run.py:98:        raise RuntimeError("pygpt_net package is not available")
src/huey/memory/PY/run.py:100:    from pygpt_net.app import run as pygpt_run
src/huey/memory/PY/run.py:102:    from huey.pygpt_net.tools.manager import MonkeyManager
src/huey/memory/PY/run.py:104:    pygpt_run(tools=[MonkeyManager()])
src/huey/memory/PY/run.py:173:        "--version", action="store_true", help="Print pygpt_net version and exit"
src/huey/memory/PY/run.py:184:        help="Select PyHuey/PyGPT-net source discovery preference",
src/huey/memory/PY/run.py:236:        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)
src/huey/memory/PY/run.py:237:    elif "PYGPT_WORKDIR" not in os.environ:
src/huey/memory/PY/run.py:238:        os.environ["PYGPT_WORKDIR"] = str(Path(__file__).resolve().parent.parent)
src/huey/memory/PY/run.py:296:        _prepare_pygpt(args.pyhuey_source)
src/huey/memory/PY/run.py:298:            from pygpt_net import __version__
src/huey/memory/PY/run.py:299:        except Exception:  # pragma: no cover - pygpt missing
src/huey/memory/PY/run.py:301:        print(f"pygpt_net version: {__version__}")
src/huey/memory/PY/set_api_keys.py:9:CONFIG_PATH = os.path.join("config", "pygpt_net", "config.json")
src/huey/memory/PY/setup.py:78:        "pygpt-net>=2.7.12",
src/huey/memory/PY/startup.py:71:        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)
src/huey/memory/PY/sync_pygpt_structure.py:4:# HueyOS: Sync Pygpt Structure module (huey/memory/PY)
src/huey/memory/PY/sync_pygpt_structure.py:14:"""Synchronize vendored pygpt-MHP files with the local project.
src/huey/memory/PY/sync_pygpt_structure.py:16:The script copies files from ``vendor/pygpt/pygpt-mhp`` into the main repository so
src/huey/memory/PY/sync_pygpt_structure.py:27:PYGPT_DIR = os.path.join("vendor", "pygpt", "pygpt-mhp")
src/huey/memory/PY/sync_pygpt_structure.py:76:        description="Copy files from the vendored pygpt-MHP mirror into the main project"
src/huey/memory/PY/sync_pygpt_structure.py:85:    mirror_tree(PYGPT_DIR, ROOT_DIR, depth=args.depth)
src/huey/memory/PY/update_prompts.py:10:INPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")
src/huey/memory/PY/update_prompts.py:11:OUTPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")  # overwrite
src/huey/memory/SH/build.sh:35:mv "$DIR_PARENT"/dist/Linux "$DIR_PARENT"/dist/pygpt-$VERSION
src/huey/memory/SH/build.sh:37:zip -r pygpt-$VERSION.zip pygpt-$VERSION -9
src/huey/memory/SH/build.sh:43:if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.zip" ]; then
src/huey/memory/SH/build.sh:44:        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.zip
src/huey/memory/SH/build.sh:47:if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.msi" ]; then
src/huey/memory/SH/build.sh:48:        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.msi
src/huey/memory/SH/clean.sh:14:Placeholder for `repo/pygpt-MHP/bin/clean.sh` from the pygpt-MHP repo.
src/huey/memory/SH/resources.sh:14:Placeholder for `repo/pygpt-MHP/bin/resources.sh` from the pygpt-MHP repo.
src/huey/memory/SH/snaprun.sh:43:python3 "$SNAP"/src/pygpt_net/app.py "$@"
src/huey/memory/SH/sort_locale.sh:14:Placeholder for `repo/pygpt-MHP/bin/sort_locale.sh` from the pygpt-MHP repo.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:241:* The software baseline is Debian 14 Forky, Python 3.13.x, PyGPT-net, and Ollama.
src/huey/memory/YAML/config.yaml:18:    - pygpt-MHP
src/huey/prompts/master-plan-v2-final.json:90:    "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v3.json:110:      "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v3.json:279:        "Run PyGPT-net and Ollama.",
src/huey/prompts/master-plan-v5.json:126:      "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v5.json:343:        "Run PyGPT-net and Ollama.",
src/huey/pygpt_custom_cli.py:4:# HueyOS: PyGPT custom CLI compatibility wrapper (src)
src/huey/pygpt_custom_cli.py:6:"""Expose the maintained CustomPyGPT implementation under :mod:`huey`.
src/huey/pygpt_custom_cli.py:9:implementation in :mod:`huey.memory.PY.pygpt_custom_cli`.
src/huey/pygpt_custom_cli.py:14:from .memory.PY import pygpt_custom_cli as _pygpt_custom_cli
src/huey/pygpt_custom_cli.py:16:__all__ = list(getattr(_pygpt_custom_cli, "__all__", ()))
src/huey/pygpt_custom_cli.py:18:globals().update({name: getattr(_pygpt_custom_cli, name) for name in __all__})
src/huey/pygpt_integration.py:4:# HueyOS: PyGPT integration compatibility wrapper (src)
src/huey/pygpt_integration.py:6:"""Expose PyHuey/PyGPT integration utilities under :mod:`huey.pygpt_integration`."""
src/huey/pygpt_integration.py:10:from .memory.PY import pygpt_integration as _pygpt_integration
src/huey/pygpt_integration.py:12:__all__ = list(getattr(_pygpt_integration, "__all__", ()))
src/huey/pygpt_integration.py:14:globals().update({name: getattr(_pygpt_integration, name) for name in __all__})
src/huey/pygpt_memory.py:7:_impl = import_module("huey.memory.PY.pygpt_memory")
src/huey/pygpt_net/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net
src/huey/pygpt_net/__init__.py:6:"""Minimal stub of the :mod:`pygpt_net` package for integration tests."""
src/huey/pygpt_net/__init__.py:21:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
src/huey/pygpt_net/__init__.py:33:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
src/huey/pygpt_net/app.py:4:# HueyOS: App module (huey/pygpt_net)
src/huey/pygpt_net/app.py:14:    """Simulate launching the PyGPT GUI with the provided tools."""
src/huey/pygpt_net/controller/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/controller
src/huey/pygpt_net/controller/__init__.py:6:"""Controller shims for mirrored PyGPT configuration modules."""
src/huey/pygpt_net/controller/agent/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/controller/agent
src/huey/pygpt_net/controller/agent/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/common.py:6:# HueyOS: Common module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/common.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/common.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/common.py:17:from pygpt_net.core.types import MODE_AGENT
src/huey/pygpt_net/controller/agent/common.py:18:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/agent/experts.py:6:# HueyOS: Experts module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/experts.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/experts.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/experts.py:19:from pygpt_net.core.bridge import BridgeContext
src/huey/pygpt_net/controller/agent/experts.py:20:from pygpt_net.core.ctx.reply import ReplyContext
src/huey/pygpt_net/controller/agent/experts.py:21:from pygpt_net.core.events import KernelEvent, RenderEvent
src/huey/pygpt_net/controller/agent/experts.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_EXPERT
src/huey/pygpt_net/controller/agent/experts.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/legacy.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/legacy.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/legacy.py:19:from pygpt_net.core.bridge import BridgeContext
src/huey/pygpt_net/controller/agent/legacy.py:20:from pygpt_net.core.ctx.reply import ReplyContext
src/huey/pygpt_net/controller/agent/legacy.py:21:from pygpt_net.core.events import KernelEvent
src/huey/pygpt_net/controller/agent/legacy.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_AGENT_LLAMA
src/huey/pygpt_net/controller/agent/legacy.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/legacy.py:24:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/agent/llama.py:6:# HueyOS: Llama module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/llama.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/llama.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/llama.py:19:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/controller/agent/llama.py:20:from pygpt_net.core.events import KernelEvent
src/huey/pygpt_net/controller/agent/llama.py:21:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/llama.py:22:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/config/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/controller/config
src/huey/pygpt_net/controller/config/__init__.py:6:"""Configuration helpers for the mirrored PyGPT controller."""
src/huey/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (huey/pygpt_net/controller/config)
src/huey/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
src/huey/pygpt_net/controller/config/placeholder.py:15:    """Provide minimal preset discovery compatible with PyGPT widgets."""
src/huey/pygpt_net/core/agents/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/core/agents
src/huey/pygpt_net/core/agents/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/legacy.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/legacy.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/legacy.py:19:from pygpt_net.core.types import (
src/huey/pygpt_net/core/agents/memory.py:6:# HueyOS: Memory module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/memory.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/memory.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/memory.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/observer/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/core/agents/observer
src/huey/pygpt_net/core/agents/observer/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/observer/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/observer/evaluation.py:6:# HueyOS: Evaluation module (huey/pygpt_net/core/agents/observer)
src/huey/pygpt_net/core/agents/observer/evaluation.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/observer/evaluation.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/observer/evaluation.py:20:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/core/agents/provider.py:6:# HueyOS: Provider module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/provider.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/provider.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/provider.py:19:from pygpt_net.provider.agents.base import BaseAgent
src/huey/pygpt_net/core/agents/runner.py:6:# HueyOS: Runner module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/runner.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/runner.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/runner.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/runner.py:21:from pygpt_net.core.bridge.worker import BridgeSignals
src/huey/pygpt_net/core/agents/runner.py:22:from pygpt_net.core.events import Event, KernelEvent
src/huey/pygpt_net/core/agents/runner.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/core/agents/runner.py:24:from pygpt_net.utils import trans
src/huey/pygpt_net/core/agents/tools.py:6:# HueyOS: Tools module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/tools.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/tools.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/tools.py:22:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/tools.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/data/config/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
src/huey/pygpt_net/data/config/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
src/huey/pygpt_net/data/config/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
src/huey/pygpt_net/item/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/item
src/huey/pygpt_net/item/preset.py:4:# HueyOS: Preset module (huey/pygpt_net/item)
src/huey/pygpt_net/item/preset.py:16:    """Minimal representation of a PyGPT preset definition."""
src/huey/pygpt_net/plugin/agent/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/plugin/agent
src/huey/pygpt_net/plugin/agent/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/plugin/agent/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/plugin/agent/__init__.py:17:from pygpt_net.core.events import Event
src/huey/pygpt_net/plugin/agent/__init__.py:18:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/plugin/agent/__init__.py:19:from pygpt_net.plugin.base.plugin import BasePlugin
src/huey/pygpt_net/plugin/agent/config.py:6:# HueyOS: Config module (huey/pygpt_net/plugin/agent)
src/huey/pygpt_net/plugin/agent/config.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/plugin/agent/config.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/plugin/agent/config.py:17:from pygpt_net.plugin.base.config import BaseConfig, BasePlugin
src/huey/pygpt_net/provider/agents/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/provider/agents
src/huey/pygpt_net/provider/agents/base.py:6:# HueyOS: Base module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/base.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/base.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai.py:6:# HueyOS: Openai module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/openai.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/openai.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai_assistant.py:6:# HueyOS: Openai Assistant module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/openai_assistant.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/openai_assistant.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai_assistant.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/provider/agents/planner.py:6:# HueyOS: Planner module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/planner.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/planner.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/react.py:6:# HueyOS: React module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/react.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/react.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/react.py:21:from pygpt_net.core.types import MODE_VISION
src/huey/pygpt_net/tools/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/tools
src/huey/pygpt_net/tools/__init__.py:6:"""Tool shims that integrate Monkey Head with the PyGPT stub."""
src/huey/pygpt_net/tools/manager.py:4:# HueyOS: Manager module (huey/pygpt_net/tools)
src/huey/pygpt_net/tools/manager.py:6:"""Minimal Monkey Head manager tool for the PyGPT stub environment."""
src/huey/pygpt_net/tools/manager.py:14:    """Expose Monkey Head automation hooks inside the PyGPT GUI."""
src/huey/pygpt_net/tools/manager/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/tools/manager
src/huey/pygpt_net/tools/manager/__init__.py:18:try:  # pragma: no cover - exercised when the full PyGPT UI is installed
src/huey/pygpt_net/tools/manager/__init__.py:19:    from pygpt_net.tools.base import BaseTool
src/huey/pygpt_net/tools/manager/__init__.py:30:try:  # pragma: no cover - exercised when the full PyGPT UI is installed
src/huey/pygpt_net/tools/manager/__init__.py:31:    from pygpt_net.utils import trans
src/huey/pygpt_net/tools/manager/__init__.py:78:    """Expose Monkey Head management tasks in the PyGPT UI."""
src/huey/pygpt_net/ui/layout/toolbox/agent.py:6:# HueyOS: Agent module (huey/pygpt_net/ui/layout/toolbox)
src/huey/pygpt_net/ui/layout/toolbox/agent.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/ui/layout/toolbox/agent.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/ui/layout/toolbox/agent.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
src/huey/pygpt_net/ui/layout/toolbox/agent.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
src/huey/pygpt_net/ui/layout/toolbox/agent.py:19:from pygpt_net.utils import trans
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:6:# HueyOS: Agent Llama module (huey/pygpt_net/ui/layout/toolbox)
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:19:from pygpt_net.utils import trans
src/huey/pyhuey_integration.py:10:from .memory.PY import pygpt_integration as _pyhuey_integration
src/hueyos/cli/commands/runtime.py:53:        help="Use the lightweight CustomPyGPT CLI without GUI dependencies.",
src/hueyos/pygpt_custom_cli.py:1:"""Compatibility module exposing :mod:`huey.pygpt_custom_cli` under :mod:`hueyos`."""
src/hueyos/pygpt_custom_cli.py:5:from huey.pygpt_custom_cli import *  # noqa: F401,F403
tests/test_custom_pygpt_cli.py:4:# HueyOS: Test Custom Pygpt Cli module (tests)
tests/test_custom_pygpt_cli.py:6:from hueyos.pygpt_custom_cli import CustomPyGPT
tests/test_custom_pygpt_cli.py:10:    bot = CustomPyGPT()
tests/test_custom_pygpt_cli.py:17:    bot = CustomPyGPT(prompt_file=prompt_file)
tests/test_custom_pygpt_cli.py:21:def test_pygpt_wrappers_export_maintained_implementation():
tests/test_custom_pygpt_cli.py:22:    from huey.memory.PY.pygpt_custom_cli import CustomPyGPT as MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:23:    from huey.pygpt_custom_cli import CustomPyGPT as HueyCustomPyGPT
tests/test_custom_pygpt_cli.py:24:    from hueyos.pygpt_custom_cli import CustomPyGPT as HueyOSCustomPyGPT
tests/test_custom_pygpt_cli.py:26:    assert HueyCustomPyGPT is MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:27:    assert HueyOSCustomPyGPT is MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:31:    bot = CustomPyGPT()
tests/test_load_cli.py:15:        if name.startswith("pygpt_net"):
tests/test_memory.py:16:from hueyos.pygpt_memory import Memory
tests/test_nltk_data_directory.py:9:from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state
tests/test_nltk_data_directory.py:17:    monkeypatch.setenv("PYGPT_NLTK_DATA_DIR", str(custom_dir))
tests/test_nltk_data_directory.py:18:    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)
tests/test_nltk_data_directory.py:20:    reset_pygpt_state()
tests/test_nltk_data_directory.py:21:    assert prepare_pygpt(source="package")
tests/test_nltk_data_directory.py:23:    module = importlib.import_module("pygpt_net")
tests/test_nltk_data_directory.py:28:        sys.modules["pygpt_net"] = module
tests/test_placeholder.py:3:from huey.pygpt_net.controller.config.placeholder import Placeholder
tests/test_pygpt_integration.py:6:from huey.pygpt_integration import (
tests/test_pygpt_integration.py:10:    prepare_pygpt,
tests/test_pygpt_integration.py:12:    reset_pygpt_state,
tests/test_pygpt_integration.py:20:    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(extra_dir))
tests/test_pygpt_integration.py:26:    assert root / "vendor" / "pygpt" / "pygpt-mhp" / "src" in paths
tests/test_pygpt_integration.py:38:def test_prepare_pygpt_uses_extra_paths(monkeypatch, tmp_path):
tests/test_pygpt_integration.py:40:    package_root = dummy_root / "pygpt_net"
tests/test_pygpt_integration.py:44:    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(dummy_root))
tests/test_pygpt_integration.py:46:    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)
tests/test_pygpt_integration.py:48:    reset_pygpt_state()
tests/test_pygpt_integration.py:49:    assert prepare_pygpt(source="extra")
tests/test_pygpt_integration.py:51:    import pygpt_net  # type: ignore
tests/test_pygpt_integration.py:53:    assert getattr(pygpt_net, "__version__", None) == "test-vendor"
tests/test_pygpt_integration.py:54:    reset_pygpt_state()
tests/test_pygpt_integration.py:58:    reset_pygpt_state()
tests/test_pygpt_integration.py:62:    assert status["module"] == "pygpt_net"
tests/test_pyhuey_manager.py:5:from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state
tests/test_pyhuey_manager.py:9:    reset_pygpt_state()
tests/test_pyhuey_manager.py:10:    assert prepare_pygpt(source="package")
tests/test_pyhuey_manager.py:12:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_pyhuey_manager.py:23:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_pyhuey_manager.py:40:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_python_compatibility.py:31:def test_pygpt_marker_allows_python_313() -> None:
tests/test_python_compatibility.py:32:    line = _get_requirement_line("pygpt-net")
tests/test_run_minimal.py:8:from hueyos.pygpt_custom_cli import CustomPyGPT
tests/test_run_minimal.py:18:    monkeypatch.setattr(CustomPyGPT, "run_cli", fake_run)
vendor/pygpt/README.md:1:# PyGPT Vendor Mirrors
vendor/pygpt/README.md:3:This directory holds lightweight PyGPT/PyGPT-net mirrors used by HueyOS tests
vendor/pygpt/README.md:9:1. the packaged compatibility tree under `src/huey/pygpt_net`,
vendor/pygpt/py-gpt/README.md:1:# PyHuey / PyGPT vendor placeholder
vendor/pygpt/py-gpt/README.md:3:This directory emulates the upstream [`py-gpt`](https://github.com/szczyglis-dev/py-gpt) submodule used by Monkey Head. It contains a lightweight `pygpt_net` compatibility stub used during the PyHuey cockpit identity migration, so the project can run and test without fetching the full upstream repository.
vendor/pygpt/py-gpt/README.md:7:- Upstream package identity and compatibility are preserved via the `pygpt-net` project name and `pygpt` console script.
vendor/pygpt/py-gpt/README.md:8:- A `pyhuey` console script is also exposed, mapped to the same entrypoint as `pygpt`.
vendor/pygpt/py-gpt/README.md:9:- This stub preserves PyGPT provenance; it is not presented as a separate published `pyhuey` package.
vendor/pygpt/py-gpt/README.md:11:If you need the full implementation, replace this directory with the real submodule checkout or install `pygpt-net` from PyPI.
vendor/pygpt/py-gpt/pyproject.toml:6:name = "pygpt-net"
vendor/pygpt/py-gpt/pyproject.toml:8:description = "PyHuey cockpit fork compatibility stub derived from upstream PyGPT (published package name remains pygpt-net)."
vendor/pygpt/py-gpt/pyproject.toml:17:"Upstream PyGPT" = "https://github.com/szczyglis-dev/py-gpt"
vendor/pygpt/py-gpt/pyproject.toml:20:pygpt = "pygpt_net:main"
vendor/pygpt/py-gpt/pyproject.toml:21:pyhuey = "pygpt_net:main"
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:1:"""Minimal stub of the :mod:`pygpt_net` package for local development.
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:28:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:40:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:67:    """Compatibility CLI entrypoint for pygpt/pyhuey console scripts."""
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:69:    print("pygpt-net vendor stub is installed (Monkey-Head-Project / PyHuey compatibility mode).")
vendor/pygpt/pygpt-mhp/README.md:1:# pygpt-MHP
vendor/pygpt/pygpt-mhp/README.md:3:This directory vendors a lightweight mirror of the PyGPT-net integration used by the
vendor/pygpt/pygpt-mhp/README.md:5:(`pip install -e repo/pygpt-MHP`) without fetching the upstream repository when working
vendor/pygpt/pygpt-mhp/pyproject.toml:6:name = "pygpt-MHP"
vendor/pygpt/pygpt-mhp/pyproject.toml:8:description = "Monkey Head Project - PyGPT integration stubs"
vendor/pygpt/pygpt-mhp/setup.cfg:2:name = pygpt-MHP
vendor/pygpt/pygpt-mhp/setup.cfg:4:description = Monkey Head Project - PyGPT integration stubs
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:6:"""Minimal stub of the :mod:`pygpt_net` package for integration tests."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:21:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:33:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
vendor/pygpt/pygpt-mhp/src/pygpt_net/app.py:4:# HueyOS: App module (repo/pygpt-MHP/src/pygpt_net)
vendor/pygpt/pygpt-mhp/src/pygpt_net/app.py:14:    """Simulate launching the PyGPT GUI with the provided tools."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py:6:"""Controller shims for mirrored PyGPT configuration modules."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller/agent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:6:# HueyOS: Common module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:17:from pygpt_net.core.types import MODE_AGENT
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:18:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:6:# HueyOS: Experts module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:19:from pygpt_net.core.bridge import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:20:from pygpt_net.core.ctx.reply import ReplyContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:21:from pygpt_net.core.events import KernelEvent, RenderEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_EXPERT
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:19:from pygpt_net.core.bridge import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:20:from pygpt_net.core.ctx.reply import ReplyContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:21:from pygpt_net.core.events import KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_AGENT_LLAMA
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:24:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:6:# HueyOS: Llama module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:19:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:20:from pygpt_net.core.events import KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:21:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:22:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller/config
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py:6:"""Configuration helpers for the mirrored PyGPT controller."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (repo/pygpt-MHP/src/pygpt_net/controller/config)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:14:    """Provide minimal preset discovery compatible with PyGPT widgets."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/core/agents
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:19:from pygpt_net.core.types import (
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:6:# HueyOS: Memory module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/core/agents/observer
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:6:# HueyOS: Evaluation module (repo/pygpt-MHP/src/pygpt_net/core/agents/observer)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:20:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:6:# HueyOS: Provider module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:19:from pygpt_net.provider.agents.base import BaseAgent
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:6:# HueyOS: Runner module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:21:from pygpt_net.core.bridge.worker import BridgeSignals
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:22:from pygpt_net.core.events import Event, KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:24:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:6:# HueyOS: Tools module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:22:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/item
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py:4:# HueyOS: Preset module (repo/pygpt-MHP/src/pygpt_net/item)
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py:16:    """Minimal representation of a PyGPT preset definition."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/plugin/agent
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:17:from pygpt_net.core.events import Event
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:18:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:19:from pygpt_net.plugin.base.plugin import BasePlugin
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:6:# HueyOS: Config module (repo/pygpt-MHP/src/pygpt_net/plugin/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:17:from pygpt_net.plugin.base.config import BaseConfig, BasePlugin
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/provider/agents
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:6:# HueyOS: Base module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:6:# HueyOS: Openai module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:6:# HueyOS: Openai Assistant module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:6:# HueyOS: Planner module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:6:# HueyOS: React module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:21:from pygpt_net.core.types import MODE_VISION
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/tools
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py:6:"""Tool shims that integrate Monkey Head with the PyGPT stub."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:4:# HueyOS: Manager module (repo/pygpt-MHP/src/pygpt_net/tools)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:6:"""Minimal Monkey Head manager tool for the PyGPT stub environment."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:14:    """Expose Monkey Head automation hooks inside the PyGPT GUI."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/tools/manager
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:13:from pygpt_net.tools.base import BaseTool
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:14:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:21:    """Expose Monkey Head management tasks in the PyGPT UI."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:6:# HueyOS: Agent module (repo/pygpt-MHP/src/pygpt_net/ui/layout/toolbox)
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:19:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:6:# HueyOS: Agent Llama module (repo/pygpt-MHP/src/pygpt_net/ui/layout/toolbox)
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:19:from pygpt_net.utils import trans

## PyGPT

.gitignore:90:config/pygpt_net/config.json
.migration/inventory/git-ls-files.pass-01.txt:72:infra/docker/docker/pygpt/Dockerfile
.migration/inventory/git-ls-files.pass-01.txt:79:integrations/pygpt/py-gpt/README.md
.migration/inventory/git-ls-files.pass-01.txt:80:integrations/pygpt/py-gpt/pyproject.toml
.migration/inventory/git-ls-files.pass-01.txt:81:integrations/pygpt/py-gpt/src/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:82:integrations/pygpt/pygpt-mhp/README.md
.migration/inventory/git-ls-files.pass-01.txt:83:integrations/pygpt/pygpt-mhp/pyproject.toml
.migration/inventory/git-ls-files.pass-01.txt:84:integrations/pygpt/pygpt-mhp/setup.cfg
.migration/inventory/git-ls-files.pass-01.txt:85:integrations/pygpt/pygpt-mhp/src/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:86:integrations/pygpt/pygpt-mhp/src/pygpt_net/app.py
.migration/inventory/git-ls-files.pass-01.txt:87:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:88:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:89:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py
.migration/inventory/git-ls-files.pass-01.txt:90:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py
.migration/inventory/git-ls-files.pass-01.txt:91:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:92:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py
.migration/inventory/git-ls-files.pass-01.txt:93:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:94:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:95:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:96:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:97:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py
.migration/inventory/git-ls-files.pass-01.txt:98:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:99:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py
.migration/inventory/git-ls-files.pass-01.txt:100:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py
.migration/inventory/git-ls-files.pass-01.txt:101:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py
.migration/inventory/git-ls-files.pass-01.txt:102:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py
.migration/inventory/git-ls-files.pass-01.txt:103:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/config.json
.migration/inventory/git-ls-files.pass-01.txt:104:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/models.json
.migration/inventory/git-ls-files.pass-01.txt:105:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/modes.json
.migration/inventory/git-ls-files.pass-01.txt:106:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_openai.json
.migration/inventory/git-ls-files.pass-01.txt:107:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_openai_assistant.json
.migration/inventory/git-ls-files.pass-01.txt:108:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_planner.json
.migration/inventory/git-ls-files.pass-01.txt:109:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/agent_react.json
.migration/inventory/git-ls-files.pass-01.txt:110:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/batman_and_joker.json
.migration/inventory/git-ls-files.pass-01.txt:111:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.agent.json
.migration/inventory/git-ls-files.pass-01.txt:112:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.agent_llama.json
.migration/inventory/git-ls-files.pass-01.txt:113:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.assistant.json
.migration/inventory/git-ls-files.pass-01.txt:114:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.audio.json
.migration/inventory/git-ls-files.pass-01.txt:115:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.chat.json
.migration/inventory/git-ls-files.pass-01.txt:116:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.completion.json
.migration/inventory/git-ls-files.pass-01.txt:117:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.expert.json
.migration/inventory/git-ls-files.pass-01.txt:118:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.img.json
.migration/inventory/git-ls-files.pass-01.txt:119:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.langchain.json
.migration/inventory/git-ls-files.pass-01.txt:120:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.llama_index.json
.migration/inventory/git-ls-files.pass-01.txt:121:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.research.json
.migration/inventory/git-ls-files.pass-01.txt:122:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/current.vision.json
.migration/inventory/git-ls-files.pass-01.txt:123:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/dalle_white_cat.json
.migration/inventory/git-ls-files.pass-01.txt:124:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/fantasy_bard.json
.migration/inventory/git-ls-files.pass-01.txt:125:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/joke_agent.json
.migration/inventory/git-ls-files.pass-01.txt:126:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/joke_expert.json
.migration/inventory/git-ls-files.pass-01.txt:127:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/mad_scientist.json
.migration/inventory/git-ls-files.pass-01.txt:128:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/noir_detective.json
.migration/inventory/git-ls-files.pass-01.txt:129:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/pirate_captain.json
.migration/inventory/git-ls-files.pass-01.txt:130:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/wild_west_cowboy.json
.migration/inventory/git-ls-files.pass-01.txt:131:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json
.migration/inventory/git-ls-files.pass-01.txt:132:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings_section.json
.migration/inventory/git-ls-files.pass-01.txt:133:integrations/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:134:integrations/pygpt/pygpt-mhp/src/pygpt_net/item/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:135:integrations/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py
.migration/inventory/git-ls-files.pass-01.txt:136:integrations/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:137:integrations/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py
.migration/inventory/git-ls-files.pass-01.txt:138:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:139:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py
.migration/inventory/git-ls-files.pass-01.txt:140:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py
.migration/inventory/git-ls-files.pass-01.txt:141:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py
.migration/inventory/git-ls-files.pass-01.txt:142:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py
.migration/inventory/git-ls-files.pass-01.txt:143:integrations/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py
.migration/inventory/git-ls-files.pass-01.txt:144:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:145:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py
.migration/inventory/git-ls-files.pass-01.txt:146:integrations/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:147:integrations/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py
.migration/inventory/git-ls-files.pass-01.txt:148:integrations/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py
.migration/inventory/git-ls-files.pass-01.txt:856:src/hueyos/pygpt_custom_cli.py
.migration/inventory/git-ls-files.pass-01.txt:857:src/hueyos/pygpt_memory.py
.migration/inventory/git-ls-files.pass-01.txt:931:src/huey/memory/BAT/pygpt-launch-&-update.bat
.migration/inventory/git-ls-files.pass-01.txt:932:src/huey/memory/BAT/pygpt-launch.bat
.migration/inventory/git-ls-files.pass-01.txt:933:src/huey/memory/BAT/pygpt-update.bat
.migration/inventory/git-ls-files.pass-01.txt:940:src/huey/memory/CSV/pygpt_prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:947:src/huey/memory/ICO/PyGPT-Huey.ico
.migration/inventory/git-ls-files.pass-01.txt:958:src/huey/memory/JSON/PyGPT_Change_Log.json
.migration/inventory/git-ls-files.pass-01.txt:1073:src/huey/memory/PDF/PYGPT (PYGPT-NET)_ A Comprehensive Report.pdf
.migration/inventory/git-ls-files.pass-01.txt:1185:src/huey/memory/PY/pygpt_custom_cli.py
.migration/inventory/git-ls-files.pass-01.txt:1186:src/huey/memory/PY/pygpt_integration.py
.migration/inventory/git-ls-files.pass-01.txt:1187:src/huey/memory/PY/pygpt_memory.py
.migration/inventory/git-ls-files.pass-01.txt:1198:src/huey/memory/PY/sync_pygpt_structure.py
.migration/inventory/git-ls-files.pass-01.txt:1347:src/huey/pygpt_integration.py
.migration/inventory/git-ls-files.pass-01.txt:1348:src/huey/pygpt_net/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1349:src/huey/pygpt_net/app.py
.migration/inventory/git-ls-files.pass-01.txt:1350:src/huey/pygpt_net/controller/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1351:src/huey/pygpt_net/controller/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1352:src/huey/pygpt_net/controller/agent/common.py
.migration/inventory/git-ls-files.pass-01.txt:1353:src/huey/pygpt_net/controller/agent/experts.py
.migration/inventory/git-ls-files.pass-01.txt:1354:src/huey/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1355:src/huey/pygpt_net/controller/agent/llama.py
.migration/inventory/git-ls-files.pass-01.txt:1356:src/huey/pygpt_net/controller/config/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1357:src/huey/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:1358:src/huey/pygpt_net/core/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1359:src/huey/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1360:src/huey/pygpt_net/core/agents/memory.py
.migration/inventory/git-ls-files.pass-01.txt:1361:src/huey/pygpt_net/core/agents/observer/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1362:src/huey/pygpt_net/core/agents/observer/evaluation.py
.migration/inventory/git-ls-files.pass-01.txt:1363:src/huey/pygpt_net/core/agents/provider.py
.migration/inventory/git-ls-files.pass-01.txt:1364:src/huey/pygpt_net/core/agents/runner.py
.migration/inventory/git-ls-files.pass-01.txt:1365:src/huey/pygpt_net/core/agents/tools.py
.migration/inventory/git-ls-files.pass-01.txt:1366:src/huey/pygpt_net/data/config/config.json
.migration/inventory/git-ls-files.pass-01.txt:1367:src/huey/pygpt_net/data/config/models.json
.migration/inventory/git-ls-files.pass-01.txt:1368:src/huey/pygpt_net/data/config/modes.json
.migration/inventory/git-ls-files.pass-01.txt:1369:src/huey/pygpt_net/data/config/presets/agent_openai.json
.migration/inventory/git-ls-files.pass-01.txt:1370:src/huey/pygpt_net/data/config/presets/agent_openai_assistant.json
.migration/inventory/git-ls-files.pass-01.txt:1371:src/huey/pygpt_net/data/config/presets/agent_planner.json
.migration/inventory/git-ls-files.pass-01.txt:1372:src/huey/pygpt_net/data/config/presets/agent_react.json
.migration/inventory/git-ls-files.pass-01.txt:1373:src/huey/pygpt_net/data/config/presets/batman_and_joker.json
.migration/inventory/git-ls-files.pass-01.txt:1374:src/huey/pygpt_net/data/config/presets/current.agent.json
.migration/inventory/git-ls-files.pass-01.txt:1375:src/huey/pygpt_net/data/config/presets/current.agent_llama.json
.migration/inventory/git-ls-files.pass-01.txt:1376:src/huey/pygpt_net/data/config/presets/current.assistant.json
.migration/inventory/git-ls-files.pass-01.txt:1377:src/huey/pygpt_net/data/config/presets/current.audio.json
.migration/inventory/git-ls-files.pass-01.txt:1378:src/huey/pygpt_net/data/config/presets/current.chat.json
.migration/inventory/git-ls-files.pass-01.txt:1379:src/huey/pygpt_net/data/config/presets/current.completion.json
.migration/inventory/git-ls-files.pass-01.txt:1380:src/huey/pygpt_net/data/config/presets/current.expert.json
.migration/inventory/git-ls-files.pass-01.txt:1381:src/huey/pygpt_net/data/config/presets/current.img.json
.migration/inventory/git-ls-files.pass-01.txt:1382:src/huey/pygpt_net/data/config/presets/current.langchain.json
.migration/inventory/git-ls-files.pass-01.txt:1383:src/huey/pygpt_net/data/config/presets/current.llama_index.json
.migration/inventory/git-ls-files.pass-01.txt:1384:src/huey/pygpt_net/data/config/presets/current.research.json
.migration/inventory/git-ls-files.pass-01.txt:1385:src/huey/pygpt_net/data/config/presets/current.vision.json
.migration/inventory/git-ls-files.pass-01.txt:1386:src/huey/pygpt_net/data/config/presets/dalle_white_cat.json
.migration/inventory/git-ls-files.pass-01.txt:1387:src/huey/pygpt_net/data/config/presets/fantasy_bard.json
.migration/inventory/git-ls-files.pass-01.txt:1388:src/huey/pygpt_net/data/config/presets/joke_agent.json
.migration/inventory/git-ls-files.pass-01.txt:1389:src/huey/pygpt_net/data/config/presets/joke_expert.json
.migration/inventory/git-ls-files.pass-01.txt:1390:src/huey/pygpt_net/data/config/presets/mad_scientist.json
.migration/inventory/git-ls-files.pass-01.txt:1391:src/huey/pygpt_net/data/config/presets/noir_detective.json
.migration/inventory/git-ls-files.pass-01.txt:1392:src/huey/pygpt_net/data/config/presets/pirate_captain.json
.migration/inventory/git-ls-files.pass-01.txt:1393:src/huey/pygpt_net/data/config/presets/wild_west_cowboy.json
.migration/inventory/git-ls-files.pass-01.txt:1394:src/huey/pygpt_net/data/config/settings.json
.migration/inventory/git-ls-files.pass-01.txt:1395:src/huey/pygpt_net/data/config/settings_section.json
.migration/inventory/git-ls-files.pass-01.txt:1396:src/huey/pygpt_net/data/prompts.csv
.migration/inventory/git-ls-files.pass-01.txt:1397:src/huey/pygpt_net/item/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1398:src/huey/pygpt_net/item/preset.py
.migration/inventory/git-ls-files.pass-01.txt:1399:src/huey/pygpt_net/plugin/agent/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1400:src/huey/pygpt_net/plugin/agent/config.py
.migration/inventory/git-ls-files.pass-01.txt:1401:src/huey/pygpt_net/provider/agents/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1402:src/huey/pygpt_net/provider/agents/base.py
.migration/inventory/git-ls-files.pass-01.txt:1403:src/huey/pygpt_net/provider/agents/openai.py
.migration/inventory/git-ls-files.pass-01.txt:1404:src/huey/pygpt_net/provider/agents/openai_assistant.py
.migration/inventory/git-ls-files.pass-01.txt:1405:src/huey/pygpt_net/provider/agents/planner.py
.migration/inventory/git-ls-files.pass-01.txt:1406:src/huey/pygpt_net/provider/agents/react.py
.migration/inventory/git-ls-files.pass-01.txt:1407:src/huey/pygpt_net/tools/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1408:src/huey/pygpt_net/tools/manager.py
.migration/inventory/git-ls-files.pass-01.txt:1409:src/huey/pygpt_net/tools/manager/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:1410:src/huey/pygpt_net/ui/layout/toolbox/agent.py
.migration/inventory/git-ls-files.pass-01.txt:1411:src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py
.migration/inventory/git-ls-files.pass-01.txt:1442:tests/test_custom_pygpt_cli.py
.migration/inventory/git-ls-files.pass-01.txt:1482:tests/test_pygpt_integration.py
.security/bandit-baseline.json:1721:    "src/huey/memory/PY/pygpt_custom_cli.py": {
.security/bandit-baseline.json:1734:    "src/huey/memory/PY/pygpt_integration.py": {
.security/bandit-baseline.json:1747:    "src/huey/memory/PY/pygpt_memory.py": {
.security/bandit-baseline.json:1890:    "src/huey/memory/PY/sync_pygpt_structure.py": {
.security/bandit-baseline.json:2241:    "src/huey/pygpt_custom_cli.py": {
.security/bandit-baseline.json:2254:    "src/huey/pygpt_integration.py": {
.security/bandit-baseline.json:2267:    "src/huey/pygpt_memory.py": {
.security/bandit-baseline.json:2280:    "src/huey/pygpt_net/__init__.py": {
.security/bandit-baseline.json:2293:    "src/huey/pygpt_net/app.py": {
.security/bandit-baseline.json:2306:    "src/huey/pygpt_net/controller/__init__.py": {
.security/bandit-baseline.json:2319:    "src/huey/pygpt_net/controller/agent/__init__.py": {
.security/bandit-baseline.json:2332:    "src/huey/pygpt_net/controller/agent/common.py": {
.security/bandit-baseline.json:2345:    "src/huey/pygpt_net/controller/agent/experts.py": {
.security/bandit-baseline.json:2358:    "src/huey/pygpt_net/controller/agent/legacy.py": {
.security/bandit-baseline.json:2371:    "src/huey/pygpt_net/controller/agent/llama.py": {
.security/bandit-baseline.json:2384:    "src/huey/pygpt_net/controller/config/__init__.py": {
.security/bandit-baseline.json:2397:    "src/huey/pygpt_net/controller/config/placeholder.py": {
.security/bandit-baseline.json:2410:    "src/huey/pygpt_net/core/agents/__init__.py": {
.security/bandit-baseline.json:2423:    "src/huey/pygpt_net/core/agents/legacy.py": {
.security/bandit-baseline.json:2436:    "src/huey/pygpt_net/core/agents/memory.py": {
.security/bandit-baseline.json:2449:    "src/huey/pygpt_net/core/agents/observer/__init__.py": {
.security/bandit-baseline.json:2462:    "src/huey/pygpt_net/core/agents/observer/evaluation.py": {
.security/bandit-baseline.json:2475:    "src/huey/pygpt_net/core/agents/provider.py": {
.security/bandit-baseline.json:2488:    "src/huey/pygpt_net/core/agents/runner.py": {
.security/bandit-baseline.json:2501:    "src/huey/pygpt_net/core/agents/tools.py": {
.security/bandit-baseline.json:2514:    "src/huey/pygpt_net/item/__init__.py": {
.security/bandit-baseline.json:2527:    "src/huey/pygpt_net/item/preset.py": {
.security/bandit-baseline.json:2540:    "src/huey/pygpt_net/plugin/agent/__init__.py": {
.security/bandit-baseline.json:2553:    "src/huey/pygpt_net/plugin/agent/config.py": {
.security/bandit-baseline.json:2566:    "src/huey/pygpt_net/provider/agents/__init__.py": {
.security/bandit-baseline.json:2579:    "src/huey/pygpt_net/provider/agents/base.py": {
.security/bandit-baseline.json:2592:    "src/huey/pygpt_net/provider/agents/openai.py": {
.security/bandit-baseline.json:2605:    "src/huey/pygpt_net/provider/agents/openai_assistant.py": {
.security/bandit-baseline.json:2618:    "src/huey/pygpt_net/provider/agents/planner.py": {
.security/bandit-baseline.json:2631:    "src/huey/pygpt_net/provider/agents/react.py": {
.security/bandit-baseline.json:2644:    "src/huey/pygpt_net/tools/__init__.py": {
.security/bandit-baseline.json:2657:    "src/huey/pygpt_net/tools/manager.py": {
.security/bandit-baseline.json:2670:    "src/huey/pygpt_net/tools/manager/__init__.py": {
.security/bandit-baseline.json:2683:    "src/huey/pygpt_net/ui/layout/toolbox/agent.py": {
.security/bandit-baseline.json:2696:    "src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py": {
.security/bandit-baseline.json:3216:    "src/hueyos/pygpt_custom_cli.py": {
.security/bandit-baseline.json:5349:      "code": "156         )\n157         subprocess.run(\n158             [sys.executable, \"sync_pygpt_structure.py\"],\n159             check=True,\n160         )\n161     except subprocess.CalledProcessError as exc:\n",
.security/bandit-baseline.json:6252:      "filename": "src/huey/pygpt_net/tools/manager/__init__.py",
.security/bandit-baseline.json:6272:      "filename": "src/huey/pygpt_net/tools/manager/__init__.py",
CHANGELOG.md:20:- PyHuey cockpit alignment phase 1: added `pyhuey` console-script alias while retaining `pygpt`, updated package description/URLs for PyHuey cockpit identity, and preserved upstream PyGPT compatibility/provenance.
CHANGELOG.md:22:- Docker alignment documented for v101.1 with HueyOS runtime expectations (`huey-api`, non-root `hueyos`, repository package install) instead of PyGPT as primary runtime.
README.md:75:| **PyGPT-net** | Aperture candidate / later lab interface | Deferred for V1; useful later when richer access/debugging is needed |
README.md:165:**PyGPT-net** is a later aperture candidate and debugging/interface surface. It is not required for V1.
README.md:197:| **PyGPT-net** | Deferred until the system needs richer interface/debug access |
README.md:529:| PyGPT-net | Too heavy and unnecessary for V1 proof |
README.md:733:## PyGPT-net posture
README.md:735:PyGPT-net is useful, but it is not required for V1.
README.md:744:PyGPT-net becomes useful later when the project needs richer interface access, debugging surfaces, and visibility into many agents or modules.
README.md:906:| PyGPT-net | Too heavy for V1; useful later for richer aperture/debugging |
README.md:1128:| **PyGPT-net** | Later aperture/interface candidate; deferred from V1. |
README.md:1202:- PyGPT-net or equivalent aperture/debugging surface,
audit-requirements.txt:108:pygpt-net==2.7.12
constraints.txt:33:pygpt-net==2.7.12
docs/_build/html/_sources/audits/v101.1-repo-control-paths.md.txt:14:- `integrations/pygpt` does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.
docs/_build/html/_sources/security/security-hardening-status.md.txt:150:- `config/pygpt_net/config.json`
docs/_build/html/audits/v101.1-repo-control-paths.html:50:<li><p><code class="docutils literal notranslate"><span class="pre">integrations/pygpt</span></code> does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.</p></li>
docs/_build/html/searchindex.js:1:Search.setIndex({"alltitles":{"1) pip-audit (Python dependency vulnerabilities)":[[3,"pip-audit-python-dependency-vulnerabilities"]],"2) Bandit (Python static security linting)":[[3,"bandit-python-static-security-linting"]],"3) Secret scanning":[[3,"secret-scanning"]],"Compatibility-path decision":[[0,"compatibility-path-decision"]],"Core Docs":[[2,null]],"Docker image pinning policy":[[3,"docker-image-pinning-policy"]],"Environment-specific guidance":[[3,"environment-specific-guidance"]],"Local security checks":[[3,"local-security-checks"]],"Monkey-Head-Project Documentation":[[2,null]],"Providing development secrets safely":[[3,"providing-development-secrets-safely"]],"Resolved hardening items":[[3,"resolved-hardening-items"]],"Runtime impact":[[0,"runtime-impact"]],"Scope and intent":[[3,"scope-and-intent"]],"Security Hardening Status":[[3,null]],"Status disclaimer":[[3,"status-disclaimer"]],"Summary of metadata-only changes":[[0,"summary-of-metadata-only-changes"]],"Token requirements by environment":[[3,"token-requirements-by-environment"]],"Unresolved or manual hardening items":[[3,"unresolved-or-manual-hardening-items"]],"VNC/noVNC safe access pattern":[[3,"vnc-novnc-safe-access-pattern"]],"v101.1 Namespace Migration Direction":[[1,null]],"v101.1 repo-control path cleanup":[[0,null]],"\u201cDo not commit\u201d list":[[3,"do-not-commit-list"]]},"docnames":["audits/v101.1-repo-control-paths","development/v101.1-namespace-migration","index","security/security-hardening-status"],"envversion":{"sphinx":65,"sphinx.domains.c":3,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":9,"sphinx.domains.index":1,"sphinx.domains.javascript":3,"sphinx.domains.math":2,"sphinx.domains.python":4,"sphinx.domains.rst":2,"sphinx.domains.std":2},"filenames":["audits\\v101.1-repo-control-paths.md","development\\v101.1-namespace-migration.md","index.rst","security\\security-hardening-status.md"],"indexentries":{},"objects":{},"objnames":{},"objtypes":{},"terms":{"03":3,"05":[0,3],"1":2,"11":0,"2026":[0,3],"A":3,"If":3,"It":3,"No":[0,1,3],"The":3,"These":3,"accept":3,"access":2,"accident":3,"action":3,"activ":[0,3],"ad":3,"add":1,"addit":3,"address":3,"adjac":3,"affect":3,"again":3,"against":3,"align":3,"alon":3,"alreadi":0,"altern":3,"an":3,"ani":3,"anomali":3,"api":[0,1,3],"app":3,"appli":3,"appropri":3,"approv":3,"ar":3,"artifact":3,"attempt":3,"auth":3,"authent":3,"avoid":3,"back":3,"base":3,"baselin":3,"bastion":3,"bearer":3,"becaus":0,"befor":3,"behavior":1,"block":3,"bootstrap":3,"bound":3,"break":3,"build":3,"cadenc":3,"canon":1,"capabl":3,"central":3,"chang":[1,2,3],"check":2,"ci":3,"cleanup":2,"cli":1,"code":[0,1,3],"codeown":0,"commit":2,"compat":[1,2],"complet":3,"compromis":3,"config":3,"confirm":[0,3],"connect":3,"consid":3,"consist":3,"contain":3,"context":3,"continu":3,"control":[2,3],"core":1,"coverag":3,"credenti":3,"critic":3,"current":3,"cve":3,"cycl":3,"data":3,"date":0,"debug":3,"decis":2,"declar":3,"dedic":3,"defens":3,"deploy":3,"depth":3,"detect":3,"dev":3,"develop":2,"differ":3,"digest":3,"direct":2,"directli":3,"directori":0,"disabl":3,"disclaim":2,"dist":3,"distribut":1,"do":2,"doc":3,"docker":2,"dockerfil":3,"document":[0,1,3],"doe":[0,1,3],"dump":3,"dure":1,"each":3,"empti":1,"enforc":3,"env":3,"environ":2,"ephemer":3,"equival":3,"establish":1,"everi":3,"evolv":3,"exampl":3,"except":3,"exclud":3,"exist":[0,1,3],"expect":3,"expir":3,"explicit":3,"explicitli":1,"export":3,"expos":3,"exposur":3,"featur":3,"file":[0,3],"firewal":3,"float":3,"follow":3,"format":3,"from":[0,3],"front":3,"full":3,"gate":3,"gatewai":3,"gener":3,"gitattribut":0,"github":0,"gitignor":3,"gitleak":3,"gitmodul":0,"glass":3,"gpt":0,"group":3,"guardrail":3,"gui":3,"guidanc":2,"ha":1,"handl":3,"hard":3,"harden":2,"high":3,"higher":3,"histori":3,"hoc":3,"hook":3,"hsm":3,"huei":[0,1],"hueyo":[1,2],"i":[0,1,3],"ident":3,"imag":2,"immedi":3,"immut":3,"impact":2,"implement":[1,3],"import":1,"incid":3,"includ":3,"infrastructur":3,"ingress":3,"inject":3,"input":3,"instal":3,"integr":[0,2,3],"intent":2,"internet":3,"introduc":3,"ip":3,"isol":3,"item":2,"json":3,"justifi":3,"keep":3,"kei":3,"keychain":3,"last":3,"layer":3,"layout":3,"leak":3,"leakag":3,"least":3,"legaci":1,"like":3,"linguist":0,"list":2,"live":3,"local":2,"locat":0,"lockfil":3,"log":3,"long":3,"lowest":3,"m":3,"maintain":[1,3],"mainten":3,"manag":3,"mandatori":3,"manual":2,"match":[0,3],"mean":3,"memori":1,"merg":3,"metadata":[2,3],"mfa":3,"migrat":2,"minim":3,"mirror":3,"moder":3,"modul":1,"monitor":3,"move":1,"must":3,"namespac":2,"nano":0,"need":3,"network":3,"never":3,"new":3,"non":3,"note":3,"novnc":2,"one":3,"ongo":3,"onli":[2,3],"open":3,"oper":3,"out":3,"output":3,"ownership":0,"packag":1,"password":3,"patch":3,"path":[2,3],"pattern":2,"period":3,"perman":3,"pick":3,"pin":2,"placehold":3,"plaintext":3,"plane":3,"point":0,"polici":2,"port":3,"possibl":3,"postur":3,"pr":3,"practic":3,"pre":3,"prefer":3,"present":3,"preserv":1,"privat":3,"privileg":3,"prod":3,"product":3,"prohibit":3,"project":3,"proven":3,"provid":2,"public":3,"purpos":3,"py":[0,1],"pygpt":0,"pygpt_net":3,"pyhuei":[0,2],"python":0,"r":3,"rather":3,"re":3,"real":[0,3],"reassess":3,"rebuild":3,"recommend":3,"record":[1,3],"recur":3,"refer":3,"registri":3,"regular":3,"relat":3,"releas":3,"relev":3,"remain":[1,3],"remedi":3,"remot":3,"remov":[0,3],"repo":[2,3],"report":3,"repositori":[0,3],"resolv":2,"respons":3,"restrict":3,"retain":0,"review":3,"revisit":3,"revoc":3,"revok":3,"risk":3,"rotat":3,"rule":[0,3],"run":3,"runtim":[1,2,3],"safe":2,"sampl":3,"scaffold":1,"scanner":3,"schedul":3,"scope":[1,2],"screenshot":3,"secret":2,"secur":2,"sensit":3,"serv":3,"servic":3,"session":3,"share":3,"shell":3,"short":3,"should":3,"site":2,"so":0,"sourc":[0,3],"specif":2,"src":[0,1],"sso":3,"stage":3,"stale":0,"statu":2,"still":3,"strategi":3,"strict":3,"strong":3,"structur":3,"style":3,"subject":3,"submodul":0,"summari":2,"support":3,"surfac":[1,3],"tag":3,"task":[1,3],"templat":3,"temporari":3,"termin":3,"test":3,"than":3,"thei":3,"thi":[0,1,2,3],"threat":3,"time":[0,3],"tl":3,"toler":3,"track":3,"trail":3,"treat":3,"troubleshoot":3,"trust":3,"tune":3,"under":[1,3],"unless":3,"unresolv":2,"until":1,"up":3,"updat":[0,3],"upgrad":3,"upstream":3,"us":3,"user":3,"v101":2,"valid":3,"valu":3,"var":3,"variabl":3,"vendor":0,"venv":3,"verbos":3,"verif":3,"verifi":3,"version":3,"via":3,"vnc":2,"vpn":3,"wa":0,"were":0,"when":3,"whenev":3,"where":3,"while":3,"window":3,"work":[2,3],"workflow":3,"workload":3,"x":3,"you":3,"zero":3},"titles":["v101.1 repo-control path cleanup","v101.1 Namespace Migration Direction","Monkey-Head-Project Documentation","Security Hardening Status"],"titleterms":{"1":[0,1,3],"2":3,"3":3,"access":3,"audit":3,"bandit":3,"chang":0,"check":3,"cleanup":0,"commit":3,"compat":0,"control":0,"core":2,"decis":0,"depend":3,"develop":3,"direct":1,"disclaim":3,"do":3,"doc":2,"docker":3,"document":2,"environ":3,"guidanc":3,"harden":3,"head":2,"imag":3,"impact":0,"intent":3,"item":3,"lint":3,"list":3,"local":3,"manual":3,"metadata":0,"migrat":1,"monkei":2,"namespac":1,"novnc":3,"onli":0,"path":0,"pattern":3,"pin":3,"pip":3,"polici":3,"project":2,"provid":3,"python":3,"repo":0,"requir":3,"resolv":3,"runtim":0,"safe":3,"scan":3,"scope":3,"secret":3,"secur":3,"specif":3,"static":3,"statu":3,"summari":0,"token":3,"unresolv":3,"v101":[0,1],"vnc":3,"vulner":3}})
docs/_build/html/security/security-hardening-status.html:221:<li><p><code class="docutils literal notranslate"><span class="pre">config/pygpt_net/config.json</span></code></p></li>
docs/audits/v101.1-dependency-source-of-truth.md:54:**Authoritative source: `pyproject.toml` for HueyOS runtime images; `pygpt-net` pin path for optional PyHuey cockpit image**
docs/audits/v101.1-dependency-source-of-truth.md:59:- `infra/docker/pyhuey/Dockerfile` intentionally installs `pygpt-net` directly for optional cockpit/provenance compatibility.
docs/audits/v101.1-dependency-source-of-truth.md:89:   - Docker optional PyHuey cockpit image: explicit `pygpt-net` install (separate intent).
docs/audits/v101.1-docker-alignment.md:4:Align the main HueyOS Docker runtime with the repository package (`hueyos`) and remove PyGPT as the primary runtime.
docs/audits/v101.1-docker-alignment.md:55:- Runtime entrypoint is `huey-api` (HueyOS API), not `pygpt`.
docs/audits/v101.1-pyhuey-branding-string-audit.md:8:- `rg -n "PyGPT|pygpt" src/huey/memory/PY src/hueyos/cli/commands/runtime.py README.md`
docs/audits/v101.1-pyhuey-branding-string-audit.md:10:## Classification of remaining `PyGPT` / `pygpt` strings
docs/audits/v101.1-pyhuey-branding-string-audit.md:14:- `README.md` references to **PyGPT-net** in architecture posture sections as lineage/deferred aperture context.
docs/audits/v101.1-pyhuey-branding-string-audit.md:15:- `src/huey/memory/PY/pygpt_integration.py` docstrings describing PyHuey as forked from PyGPT/PyGPT-net.
docs/audits/v101.1-pyhuey-branding-string-audit.md:19:- `pygpt_net` import/module references across runtime and integration code paths.
docs/audits/v101.1-pyhuey-branding-string-audit.md:20:- `config/pygpt_net/config.json` paths in installer/config helper modules.
docs/audits/v101.1-pyhuey-branding-string-audit.md:21:- CLI version output text: `pygpt_net version: ...` in `src/huey/memory/PY/run.py`.
docs/audits/v101.1-pyhuey-branding-string-audit.md:25:- Additional user-facing references in optional installer scripts and legacy/deferred docs that still print "PyGPT/PyGPT-net" where PyHuey wording may be more appropriate.
docs/audits/v101.1-pyhuey-branding-string-audit.md:26:- Vendored/compatibility tree wording under legacy `pygpt_*` filenames that should be reviewed only when import compatibility is formally migrated.
docs/audits/v101.1-pyhuey-identity-phase1.md:4:Scope: `vendor/pygpt/py-gpt` compatibility stub
docs/audits/v101.1-pyhuey-identity-phase1.md:8:1. Added `pyhuey` console script alias while retaining `pygpt`.
docs/audits/v101.1-pyhuey-identity-phase1.md:9:2. Kept published package metadata name as `pygpt-net` for compatibility.
docs/audits/v101.1-pyhuey-identity-phase1.md:11:4. Added project URLs for Monkey-Head-Project/PyHuey and upstream PyGPT provenance.
docs/audits/v101.1-pyhuey-identity-phase1.md:16:- `pygpt-net` package name remains unchanged in metadata.
docs/audits/v101.1-pyhuey-identity-phase1.md:17:- `pygpt` console script remains available.
docs/audits/v101.1-pyhuey-identity-phase1.md:18:- `pyhuey` points to the same runtime entrypoint as `pygpt`.
docs/audits/v101.1-pyhuey-identity-phase1.md:19:- Upstream PyGPT origin is explicitly cited in README and project URLs.
docs/audits/v101.1-pyhuey-identity-phase1.md:25:- GUI/runtime feature parity with upstream PyGPT.
docs/audits/v101.1-repo-control-paths.md:14:- `integrations/pygpt` does not exist in this repository at this time, so no compatibility ownership or vendored-path metadata was retained for it.
docs/legal/provenance-and-licenses.md:27:- `vendor/pygpt/README.md` states runtime integration order that includes `integrations/pyhuey` and identifies `vendor/pygpt` as static mirrors.
docs/legal/provenance-and-licenses.md:32:## 4) Upstream PyGPT provenance
docs/legal/provenance-and-licenses.md:34:Repository docs already describe PyHuey as derived from upstream PyGPT/PyGPT-net:
docs/legal/provenance-and-licenses.md:36:- `infra/docker/pyhuey/README.md` explicitly says the cockpit image is derived from upstream `pygpt-net` for provenance/compatibility.
docs/legal/provenance-and-licenses.md:37:- `vendor/pygpt/README.md` labels the vendored content as PyGPT/PyGPT-net mirrors.
docs/legal/provenance-and-licenses.md:45:1. **Do not copy code** between Monkey-Head-Project core paths and PyHuey/PyGPT-derived paths without preserving original copyright and license notices.
docs/legal/provenance-and-licenses.md:47:3. **Keep integration paths explicit** (`integrations/pyhuey`, `vendor/pygpt`) so reviewers can distinguish first-party code from fork/vendor code.
docs/security/api-secret-handling.md:13:4. **Local fallback file** `config/pygpt_net/config.json` only when necessary.
docs/security/api-secret-handling.md:17:- Treat `config/pygpt_net/config.json` as **local-only**.
docs/security/security-hardening-status.md:150:- `config/pygpt_net/config.json`
docs/security/tool_permission_boundaries.md:3:This note documents execution boundaries for `huey.pygpt_net.tools.manager.MonkeyManager`.
docs/unsorted/CONTRIBUTING.md:203:- Development: `integrations/pyhuey` tracks the full PyHuey source; `vendor/pygpt/pygpt-mhp` holds the lightweight mirror.
docs/unsorted/repository-restructure-inventory.md:30:- `repo/pygpt-MHP/` + `repo/py-gpt/` ΓåÆ `vendor/pygpt/`
docs/unsorted/repository-restructure-inventory.md:40:- `repo/py-gpt` and `repo/pygpt-MHP` should be consolidated under a single naming scheme (`vendor/pygpt/`).
docs/unsorted/repository-restructure-inventory.md:42:- `src/huey/pygpt_net` naming should be aligned with integration folder naming (`pygpt_net` vs `pygpt`).
docs/unsorted/repository-restructure-recommendation.md:34:ΓööΓöÇΓöÇ vendor/                  # vendored third-party dependencies and PyGPT mirrors
infra/docker/Dockerfile.vnc:1:FROM pygpt:local
infra/docker/Dockerfile.vnc:16:RUN cat > /usr/local/bin/start-vnc-pygpt.sh <<'EOF'
infra/docker/Dockerfile.vnc:56:# Launch PyGPT
infra/docker/Dockerfile.vnc:57:exec pygpt --workdir=/data
infra/docker/Dockerfile.vnc:60:RUN chmod +x /usr/local/bin/start-vnc-pygpt.sh
infra/docker/Dockerfile.vnc:62:# Run as the non-root user that exists in pygpt:local
infra/docker/Dockerfile.vnc:63:USER pygpt
infra/docker/Dockerfile.vnc:64:WORKDIR /home/pygpt
infra/docker/Dockerfile.vnc:67:CMD ["/usr/local/bin/start-vnc-pygpt.sh"]
infra/docker/docker/pygpt/Dockerfile:16:RUN useradd -m -u 1000 pygpt
infra/docker/docker/pygpt/Dockerfile:17:USER pygpt
infra/docker/docker/pygpt/Dockerfile:18:ENV HOME=/home/pygpt \
infra/docker/docker/pygpt/Dockerfile:21:# Install PyGPT from PyPI
infra/docker/docker/pygpt/Dockerfile:23: && pip install --no-cache-dir pygpt-net
infra/docker/docker/pygpt/Dockerfile:25:# PyGPT stores config/data in its workdir; we'll default to /data
infra/docker/docker/pygpt/Dockerfile:26:ENTRYPOINT ["pygpt"]
infra/docker/pyhuey/Dockerfile:3:# Optional PyHuey cockpit/tooling image derived from upstream PyGPT runtime.
infra/docker/pyhuey/Dockerfile:23: && pip install --no-cache-dir pygpt-net
infra/docker/pyhuey/Dockerfile:29:ENTRYPOINT ["pygpt"]
infra/docker/pyhuey/README.md:10:  upstream `pygpt-net` for provenance and compatibility).
infra/docker/pyhuey/README.md:17:PyHuey cockpit packaging here preserves upstream PyGPT provenance by installing
infra/docker/pyhuey/README.md:18:`pygpt-net` and retaining the upstream `pygpt` entrypoint for compatibility.
master-plan-v101.1.json:6:  "description": "Master Plan V101.1: PyHuey cockpit alignment release. V101.1 preserves the V101.0 Legion Go / Huey Brain V1 scope lock while adding PyHuey as the project-controlled fork of PyGPT and the Windows 11 Pro cockpit/build/runtime surface for Huey. It standardizes repository paths around integrations/pyhuey and platform/windows/huey, records Python 3.13 as the Windows Huey/PyHuey target branch, keeps Windows/PyHuey out of Huey Brain sovereignty, and treats docs, website, GitHub/README, and the master plan as the human-readable build-record surfaces.",
master-plan-v101.1.json:82:    "pygpt_net_role",
master-plan-v101.1.json:128:      "Atlas should prevent V1 from drifting into Huey Body actuation, live microphone work, enclosure modification, distributed compute, HIMS runtime, PyGPT-net, or full governance implementation.",
master-plan-v101.1.json:143:      "Do not reactivate PyGPT-net, HIMS, multi-agent governance, or Huey Body actuation inside V1 unless Dylan explicitly reopens scope.",
master-plan-v101.1.json:310:      "PyGPT-net or richer aperture after CLI/queue proof stabilizes.",
master-plan-v101.1.json:347:      "PyHuey": "Windows 11 Pro cockpit/build/runtime tooling forked from PyGPT; active as LabTech/cockpit integration surface, not the V1 proof runtime."
master-plan-v101.1.json:364:      "PyGPT_net": "Later aperture/debugging surface, not V1.",
master-plan-v101.1.json:396:      "Keep Huey Body, live microphone, wake word, PyGPT-net, HIMS runtime, governance runtime, and distributed compute out of V1."
master-plan-v101.1.json:408:    "conflict_policy": "If older docs describe Huey Core as the current proof body, place cognition on the Body, activate PyGPT-net/HIMS/governance in V1, or distribute V1 compute, preserve them as history and implement V101.0 unless Dylan explicitly reopens scope.",
master-plan-v101.1.json:427:        "PyHuey is the project-controlled fork of PyGPT and the Windows 11 Pro cockpit for Huey.",
master-plan-v101.1.json:444:      "integrations/pyhuey": "Source fork of PyGPT renamed PyHuey for project-facing cockpit work.",
master-plan-v101.1.json:445:      "integrations/pygpt": "Allowed short-term alias only if tooling expects the upstream name; not the preferred V101.1 path.",
master-plan-v101.1.json:477:      "PyGPT-net": "Deferred aperture / diagnostic interface candidate; not V1 infrastructure.",
master-plan-v101.1.json:480:      "PyHuey": "Project-controlled fork of PyGPT; Windows 11 Pro cockpit, integration-test surface, and build/runtime tooling for Huey. Active as cockpit/tooling, not Huey Brain sovereignty or V1 proof runtime.",
master-plan-v101.1.json:481:      "PyGPT / PyGPT-net": "Upstream/source-lineage name and historical aperture wording. The active project-facing fork name is PyHuey."
master-plan-v101.1.json:489:      "Use PyHuey as the project-facing name for the forked PyGPT cockpit.",
master-plan-v101.1.json:490:      "Use integrations/pyhuey as the preferred source fork path; integrations/pygpt is only a compatibility alias.",
master-plan-v101.1.json:515:      "PyGPT-net as primary aperture",
master-plan-v101.1.json:595:    "pygpt_net": {
master-plan-v101.1.json:601:      "role": "project-controlled PyGPT fork and Windows 11 Pro cockpit for Huey",
master-plan-v101.1.json:603:      "responsibility": "provide controlled Windows cockpit, provider/tool testing, PyGPT-derived interface work, Redis/vector-store patch experimentation, launch/build scripts, and reproducible Python 3.13 freezes.",
master-plan-v101.1.json:662:      "python": "Python 3.13.x target branch; current proof used Python 3.13.13 in Venvs/PyGPT.",
master-plan-v101.1.json:665:      "venv_policy": "Project venv may remain Venvs/PyGPT locally during transition, but repository-facing name is PyHuey.",
master-plan-v101.1.json:885:      "PyGPT-net GUI or aperture layer",
master-plan-v101.1.json:1029:  "pygpt_net_role": {
master-plan-v101.1.json:1030:    "name": "PyGPT / PyGPT-net",
master-plan-v101.1.json:1033:    "v101_1_decision": "Fork PyGPT as PyHuey. Use PyHuey for the project cockpit and controlled Windows 11 Pro Python 3.13 branch. Keep PyGPT/PyGPT-net as upstream/source-lineage terminology.",
master-plan-v101.1.json:1770:      "logical_session_path": "Portal terminal -> SSH transport -> Huey-side portal bridge -> PyGPT-net aperture -> HIMS -> internal deliberation or execution path"
master-plan-v101.1.json:1792:      "huey_side": "Huey computation, memory, PyGPT-net, HIMS, and governance continue to live on the Debian / HueyOS side.",
master-plan-v101.1.json:2129:        "PyGPT-net or HIMS is introduced to replace the simple pipeline.",
master-plan-v101.1.json:2158:      "future": "live mic, body actuation, HIMS, PyGPT-net, and governance are reintroduced only after V1 is stable."
master-plan-v101.1.json:2176:    "Clarify the future role of PyGPT-net once the Legion Go pipeline succeeds.",
master-plan-v101.1.json:2325:      "Moved PyGPT-net out of V1 and into deferred aperture/debugging status.",
master-plan-v101.1.json:2369:      "Added Windows stack policy: Windows 10/11, WSL, and PyGPT are LabTech/cockpit/fallback layers, not Huey sovereignty.",
master-plan-v101.1.json:2391:    "Do not reintroduce PyGPT-net, HIMS, live mic, body actuation, or governance runtime until the Legion Go loop is proven.",
master-plan-v101.1.json:2400:    "Windows 10/11, WSL, and PyGPT are LabTech/cockpit/fallback layers, not Huey sovereignty.",
master-plan-v101.1.json:2472:      "Kept Huey Body, HIMS runtime, PyGPT-net, live microphone input, governance runtime, and Farm compute deferred."
master-plan-v101.1.json:2488:      "Preserved the V100.9 scope lock: stock Legion Go, controlled MP3 fixtures, faster-whisper, API bridge, structured logging, no Body/HIMS/PyGPT-net/governance/live mic/distributed compute in V1."
master-plan-v101.1.json:2521:        "PyGPT-net",
master-plan-v101.1.json:2591:      "PyHuey": "forked PyGPT cockpit, Python 3.13 Windows branch, controlled update cycle",
master-plan-v101.1.json:2606:      "integrations/pyhuey": "source fork of PyGPT; preferred V101.1 path",
master-plan-v101.1.json:2607:      "integrations/pygpt": "temporary compatibility alias only if needed",
master-plan-v101.1.json:2659:      "decision": "Windows 10/11, WSL, and PyGPT work are LabTech/cockpit/fallback layers.",
master-plan-v101.1.json:2660:      "rule": "Do not let Windows, WSL, or PyGPT become Huey sovereignty by implication."
master-plan-v101.1.json:2690:    "basis": "Fork of PyGPT / PyGPT-net for project-controlled cockpit work.",
master-plan-v101.1.json:2693:    "temporary_alias": "integrations/pygpt only if needed by tooling or transition scripts",
master-plan-v101.1.json:2705:      "baseline": "Python 3.13 PyGPT/PyHuey venv reached pip check clean and passed core import tests.",
master-plan-v101.1.json:2714:    "update_policy": "Control the update cycle through the PyHuey fork. Upstream PyGPT changes should be pulled deliberately, tested against the Windows 11 Pro/Python 3.13 branch, and tagged before promotion."
master-plan-v101.1.json:2717:    "integrations/pyhuey": "PyHuey source fork of PyGPT, controlled by the project.",
master-plan-v101.1.json:2725:    "Fork PyGPT as PyHuey.",
master-plan-v101.1.json:2727:    "Use integrations/pyhuey as the preferred source fork path; integrations/pygpt is a temporary compatibility alias only.",
platform/installers/debian/Debian/install-deb.sh:21:CONFIG_DIR="$INSTALL_DIR/config/pygpt_net"
platform/installers/debian/Debian/install-deb.sh:264:    echo "Installing audio runtime packages for PyGPT/PyGPT-net ..."
platform/installers/debian/Debian/install-deb.sh:382:    echo "Installing PyGPT-net and audio Python dependencies ..."
platform/installers/debian/Debian/install-deb.sh:383:    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile
platform/installers/debian/Debian/install-deb.sh:385:    local submodule_path="$PROJECT_ROOT/vendor/pygpt/pygpt-mhp"
platform/installers/debian/Debian/install-deb.sh:387:        echo "Installing local pygpt-MHP integration in editable mode ..."
platform/installers/debian/Debian/install-deb.sh:394:    echo "Synchronising pygpt structure ..."
platform/installers/debian/Debian/install-deb.sh:395:    "$python_bin" "$PROJECT_ROOT/huey/memory/PY/sync_pygpt_structure.py" || \
platform/installers/debian/Debian/install-deb.sh:396:        echo "Warning: sync_pygpt_structure.py failed"
platform/installers/debian/Debian/install-deb.sh:452:config_path = Path(os.environ.get("HUEYOS_CONFIG_FILE", "/opt/hueyos/config/pygpt_net/config.json"))
platform/installers/debian/Debian/update-deb.sh:192:    echo "Ensuring audio runtime packages for PyGPT/PyGPT-net are installed ..."
platform/installers/debian/Debian/update-deb.sh:277:    echo "Updating PyGPT-net and audio Python dependencies ..."
platform/installers/debian/Debian/update-deb.sh:278:    "$pip_bin" install --upgrade "pygpt-net>=2.6.67" pydub sounddevice soundfile
platform/installers/debian/Debian/update-deb.sh:280:    local submodule_path="$project_root/vendor/pygpt/pygpt-mhp"
platform/installers/debian/Debian/update-deb.sh:282:        echo "Reinstalling local pygpt-MHP integration in editable mode ..."
platform/installers/debian/Debian/update-deb.sh:316:    if [[ -f "$project_root/huey/memory/PY/sync_pygpt_structure.py" ]]; then
platform/installers/debian/Debian/update-deb.sh:317:        echo "Synchronising pygpt structure ..."
platform/installers/debian/Debian/update-deb.sh:318:        "$py_bin" "$project_root/huey/memory/PY/sync_pygpt_structure.py" || \
platform/installers/debian/Debian/update-deb.sh:319:            echo "Warning: sync_pygpt_structure.py failed" >&2
platform/installers/macos/macOS/install-mac.sh:399:  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
platform/installers/macos/macOS/install-mac.sh:400:    log "Installing local package: vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/install-mac.sh:401:    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/install-mac.sh:403:    warn "Local package vendor/pygpt/pygpt-mhp not found (skipping editable install)."
platform/installers/macos/macOS/install-mac.sh:408:  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
platform/installers/macos/macOS/install-mac.sh:410:    python "$INSTALL_DIR/sync_pygpt_structure.py"
platform/installers/macos/macOS/install-mac.sh:412:    [[ "$VERBOSE" -eq 1 ]] && warn "sync_pygpt_structure.py not found (skipping)."
platform/installers/macos/macOS/update-mac.sh:367:  if [[ -d "$INSTALL_DIR/vendor/pygpt/pygpt-mhp" ]]; then
platform/installers/macos/macOS/update-mac.sh:368:    python -m pip install -e "$INSTALL_DIR/vendor/pygpt/pygpt-mhp"
platform/installers/macos/macOS/update-mac.sh:370:    [[ "$VERBOSE" -eq 1 ]] && warn "Local package vendor/pygpt/pygpt-mhp not found (skipping)."
platform/installers/macos/macOS/update-mac.sh:375:  if [[ -f "$INSTALL_DIR/sync_pygpt_structure.py" ]]; then
platform/installers/macos/macOS/update-mac.sh:377:    python "$INSTALL_DIR/sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.bat:167:REM Logic from 01-FULL.bat: setupPythonEnv + sync_pygpt_structure.py + connectivity check
platform/installers/windows/Windows/install-win.bat:408:if exist "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp" (
platform/installers/windows/Windows/install-win.bat:409:    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/install-win.bat:410:    call :checkError "Install pygpt-MHP"
platform/installers/windows/Windows/install-win.bat:412:    echo [INFO] vendor\pygpt\pygpt-mhp not found; skipping editable install.
platform/installers/windows/Windows/install-win.bat:415:if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
platform/installers/windows/Windows/install-win.bat:416:    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.ps1:486:  # Install vendored pygpt-MHP package (if present)
platform/installers/windows/Windows/install-win.ps1:487:  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/install-win.ps1:488:  if (Test-Path -LiteralPath $pygptPath) {
platform/installers/windows/Windows/install-win.ps1:489:    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir
platform/installers/windows/Windows/install-win.ps1:491:    Write-Log "Vendor path not found (vendor\pygpt\pygpt-mhp). Skipping editable install." 'WARN'
platform/installers/windows/Windows/install-win.ps1:495:  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
platform/installers/windows/Windows/install-win.ps1:499:    Write-Log "sync_pygpt_structure.py not found; skipping." 'WARN'
platform/installers/windows/Windows/update-win.bat:292:if exist "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp" (
platform/installers/windows/Windows/update-win.bat:293:    echo Installing pygpt-MHP editable...
platform/installers/windows/Windows/update-win.bat:294:    "%VENV_PY%" -m pip install -e "%INSTALL_DIR%\vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/update-win.bat:295:    call :checkError "Install pygpt-MHP"
platform/installers/windows/Windows/update-win.bat:298:if exist "%INSTALL_DIR%\sync_pygpt_structure.py" (
platform/installers/windows/Windows/update-win.bat:299:    "%VENV_PY%" "%INSTALL_DIR%\sync_pygpt_structure.py"
platform/installers/windows/Windows/update-win.ps1:391:  $pygptPath = Join-Path $InstallDir "vendor\pygpt\pygpt-mhp"
platform/installers/windows/Windows/update-win.ps1:392:  if (Test-Path -LiteralPath $pygptPath) {
platform/installers/windows/Windows/update-win.ps1:393:    Invoke-Native -Exe $venvPip -Args @("install","-e",$pygptPath) -WorkingDirectory $InstallDir -AllowNonZero
platform/installers/windows/Windows/update-win.ps1:396:  $syncScript = Join-Path $InstallDir "sync_pygpt_structure.py"
pyproject.toml:116:  "pygpt-net==2.7.12",
requirements.txt:109:pygpt-net==2.7.12
scripts/check_canon_terms.py:117:def _should_flag_pygpt(line: str) -> bool:
scripts/check_canon_terms.py:118:    if not re.search(r"\\bPyGPT\\b", line):
scripts/check_canon_terms.py:141:            if _should_flag_pygpt(line):
scripts/check_canon_terms.py:143:                    f"{path}:{lineno}: Use PyHuey as the active cockpit name; keep PyGPT for provenance only."
scripts/check_repo_drift.py:74:        name="docker-primary-pygpt",
scripts/check_repo_drift.py:75:        pattern=re.compile(r"\b(pygpt|pygpt-net)\b", re.IGNORECASE),
scripts/check_repo_drift.py:76:        message="Do not present PyGPT as the primary runtime in main Dockerfiles; use hueyos/HueyOS runtime entrypoints.",
scripts/check_repo_drift.py:137:    if rule.name == "docker-primary-pygpt":
scripts/check_repo_drift.py:157:                name="integrations-pygpt-path",
scripts/check_repo_drift.py:158:                pattern=re.compile(r"\bintegrations/pygpt\b"),
src/huey/__init__.py:21:    "pygpt_integration",
src/huey/memory/BAT/01-FULL.bat:150:pip install -e vendor\pygpt\pygpt-mhp
src/huey/memory/BAT/01-FULL.bat:151:call :checkError "Install pygpt-MHP"
src/huey/memory/BAT/01-FULL.bat:152:python sync_pygpt_structure.py
src/huey/memory/BAT/build.bat:14:Placeholder for `repo/pygpt-MHP/bin/build.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_all.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_all.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_installer.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_installer.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/pygpt-launch-&-update.bat:4:REM HueyOS: Pygpt Launch & Update batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-launch-&-update.bat:14:python -m pip install --upgrade pygpt-MHP
src/huey/memory/BAT/pygpt-launch-&-update.bat:15:pygpt
src/huey/memory/BAT/pygpt-launch.bat:4:REM HueyOS: Pygpt Launch batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-launch.bat:14:pygpt
src/huey/memory/BAT/pygpt-update.bat:4:REM HueyOS: Pygpt Update batch script (huey/memory/BAT)
src/huey/memory/BAT/pygpt-update.bat:14:python -m pip install --upgrade pygpt-MHP
src/huey/memory/DOCKER/Dockerfile:31:# Install PyGPT
src/huey/memory/DOCKER/Dockerfile:33: && pip install --no-cache-dir pygpt-net
src/huey/memory/DOCKER/Dockerfile:36:RUN useradd -m -u 1000 pygpt \
src/huey/memory/DOCKER/Dockerfile:38: && chown -R pygpt:pygpt /data
src/huey/memory/DOCKER/Dockerfile:40:USER pygpt
src/huey/memory/DOCKER/Dockerfile:41:WORKDIR /home/pygpt
src/huey/memory/DOCKER/Dockerfile:46:ENTRYPOINT ["pygpt"]
src/huey/memory/DOCKER/Dockerfile.vnc:1:FROM pygpt:local
src/huey/memory/DOCKER/Dockerfile.vnc:20:# - Runs PyGPT as non-root user "pygpt"
src/huey/memory/DOCKER/Dockerfile.vnc:21:RUN cat > /usr/local/bin/start-vnc-pygpt.sh <<'EOF'
src/huey/memory/DOCKER/Dockerfile.vnc:67:  echo "[start-vnc-pygpt] Generated VNC password: ${VNC_PASSWORD}"
src/huey/memory/DOCKER/Dockerfile.vnc:80:# Run PyGPT as non-root
src/huey/memory/DOCKER/Dockerfile.vnc:81:exec pygpt --workdir=/data
src/huey/memory/DOCKER/Dockerfile.vnc:85:RUN sed -i 's/\r$//' /usr/local/bin/start-vnc-pygpt.sh \
src/huey/memory/DOCKER/Dockerfile.vnc:86: && chmod +x /usr/local/bin/start-vnc-pygpt.sh
src/huey/memory/DOCKER/Dockerfile.vnc:89:USER pygpt
src/huey/memory/DOCKER/Dockerfile.vnc:90:ENTRYPOINT ["/usr/local/bin/start-vnc-pygpt.sh"]
src/huey/memory/JSON/PyGPT_Change_Log.json:31:        "Audio output switched from PyGame to PyAudio. It may be necessary to manually connect Alsa in Snap version with: \"sudo snap connect pygpt:alsa\".",
src/huey/memory/JSON/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
src/huey/memory/JSON/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
src/huey/memory/JSON/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
src/huey/memory/MD/duplicate-files.md:19:  - `repo/pygpt-MHP/src/pygpt_net/data/config/settings_section.json`
src/huey/memory/MD/duplicate-files.md:21:  - `src/huey/pygpt_net/data/config/settings_section.json`
src/huey/memory/MD/duplicate-files.md:25:  - `repo/pygpt-MHP/src/pygpt_net/data/config/settings.json`
src/huey/memory/MD/duplicate-files.md:27:  - `src/huey/pygpt_net/data/config/settings.json`
src/huey/memory/MD/duplicate-files.md:31:  - `repo/pygpt-MHP/src/pygpt_net/data/config/models.json`
src/huey/memory/MD/duplicate-files.md:33:  - `src/huey/pygpt_net/data/config/models.json`
src/huey/memory/MD/duplicate-files.md:37:  - `repo/pygpt-MHP/src/pygpt_net/data/config/modes.json`
src/huey/memory/MD/duplicate-files.md:39:  - `src/huey/pygpt_net/data/config/modes.json`
src/huey/memory/MD/duplicate-files.md:43:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.research.json`
src/huey/memory/MD/duplicate-files.md:45:  - `src/huey/pygpt_net/data/config/presets/current.research.json`
src/huey/memory/MD/duplicate-files.md:49:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/joke_expert.json`
src/huey/memory/MD/duplicate-files.md:51:  - `src/huey/pygpt_net/data/config/presets/joke_expert.json`
src/huey/memory/MD/duplicate-files.md:55:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.agent_llama.json`
src/huey/memory/MD/duplicate-files.md:57:  - `src/huey/pygpt_net/data/config/presets/current.agent_llama.json`
src/huey/memory/MD/duplicate-files.md:61:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.img.json`
src/huey/memory/MD/duplicate-files.md:63:  - `src/huey/pygpt_net/data/config/presets/current.img.json`
src/huey/memory/MD/duplicate-files.md:67:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.assistant.json`
src/huey/memory/MD/duplicate-files.md:69:  - `src/huey/pygpt_net/data/config/presets/current.assistant.json`
src/huey/memory/MD/duplicate-files.md:73:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.chat.json`
src/huey/memory/MD/duplicate-files.md:75:  - `src/huey/pygpt_net/data/config/presets/current.chat.json`
src/huey/memory/MD/duplicate-files.md:79:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_react.json`
src/huey/memory/MD/duplicate-files.md:81:  - `src/huey/pygpt_net/data/config/presets/agent_react.json`
src/huey/memory/MD/duplicate-files.md:85:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/batman_and_joker.json`
src/huey/memory/MD/duplicate-files.md:87:  - `src/huey/pygpt_net/data/config/presets/batman_and_joker.json`
src/huey/memory/MD/duplicate-files.md:91:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/dalle_white_cat.json`
src/huey/memory/MD/duplicate-files.md:93:  - `src/huey/pygpt_net/data/config/presets/dalle_white_cat.json`
src/huey/memory/MD/duplicate-files.md:97:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_planner.json`
src/huey/memory/MD/duplicate-files.md:99:  - `src/huey/pygpt_net/data/config/presets/agent_planner.json`
src/huey/memory/MD/duplicate-files.md:103:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.completion.json`
src/huey/memory/MD/duplicate-files.md:105:  - `src/huey/pygpt_net/data/config/presets/current.completion.json`
src/huey/memory/MD/duplicate-files.md:109:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.llama_index.json`
src/huey/memory/MD/duplicate-files.md:111:  - `src/huey/pygpt_net/data/config/presets/current.llama_index.json`
src/huey/memory/MD/duplicate-files.md:115:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.vision.json`
src/huey/memory/MD/duplicate-files.md:117:  - `src/huey/pygpt_net/data/config/presets/current.vision.json`
src/huey/memory/MD/duplicate-files.md:121:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.audio.json`
src/huey/memory/MD/duplicate-files.md:123:  - `src/huey/pygpt_net/data/config/presets/current.audio.json`
src/huey/memory/MD/duplicate-files.md:127:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.expert.json`
src/huey/memory/MD/duplicate-files.md:129:  - `src/huey/pygpt_net/data/config/presets/current.expert.json`
src/huey/memory/MD/duplicate-files.md:133:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/joke_agent.json`
src/huey/memory/MD/duplicate-files.md:135:  - `src/huey/pygpt_net/data/config/presets/joke_agent.json`
src/huey/memory/MD/duplicate-files.md:139:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.agent.json`
src/huey/memory/MD/duplicate-files.md:141:  - `src/huey/pygpt_net/data/config/presets/current.agent.json`
src/huey/memory/MD/duplicate-files.md:145:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_openai_assistant.json`
src/huey/memory/MD/duplicate-files.md:147:  - `src/huey/pygpt_net/data/config/presets/agent_openai_assistant.json`
src/huey/memory/MD/duplicate-files.md:151:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/current.langchain.json`
src/huey/memory/MD/duplicate-files.md:153:  - `src/huey/pygpt_net/data/config/presets/current.langchain.json`
src/huey/memory/MD/duplicate-files.md:157:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/agent_openai.json`
src/huey/memory/MD/duplicate-files.md:159:  - `src/huey/pygpt_net/data/config/presets/agent_openai.json`
src/huey/memory/MD/duplicate-files.md:163:  - `repo/pygpt-MHP/src/pygpt_net/data/prompts.csv`
src/huey/memory/MD/duplicate-files.md:164:  - `src/huey/pygpt_net/data/prompts.csv`
src/huey/memory/MD/duplicate-files.md:168:  - `repo/pygpt-MHP/src/pygpt_net/data/config/config.json`
src/huey/memory/MD/duplicate-files.md:169:  - `src/huey/pygpt_net/data/config/config.json`
src/huey/memory/MD/duplicate-files.md:173:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/pirate_captain.json`
src/huey/memory/MD/duplicate-files.md:174:  - `src/huey/pygpt_net/data/config/presets/pirate_captain.json`
src/huey/memory/MD/duplicate-files.md:178:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/wild_west_cowboy.json`
src/huey/memory/MD/duplicate-files.md:179:  - `src/huey/pygpt_net/data/config/presets/wild_west_cowboy.json`
src/huey/memory/MD/duplicate-files.md:183:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/mad_scientist.json`
src/huey/memory/MD/duplicate-files.md:184:  - `src/huey/pygpt_net/data/config/presets/mad_scientist.json`
src/huey/memory/MD/duplicate-files.md:188:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/noir_detective.json`
src/huey/memory/MD/duplicate-files.md:189:  - `src/huey/pygpt_net/data/config/presets/noir_detective.json`
src/huey/memory/MD/duplicate-files.md:193:  - `repo/pygpt-MHP/src/pygpt_net/data/config/presets/fantasy_bard.json`
src/huey/memory/MD/duplicate-files.md:194:  - `src/huey/pygpt_net/data/config/presets/fantasy_bard.json`
src/huey/memory/MD/placeholder-occurrences.md:9:- `repo/py-gpt/src/pygpt_net/__init__.py`:3 - `This placeholder mirrors the directory layout of the upstream `py-gpt``
src/huey/memory/MD/placeholder-occurrences.md:10:- `repo/pygpt-MHP/src/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:11:- `repo/pygpt-MHP/src/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:12:- `src/huey/memory/CSV/pygpt_prompts.csv`:133 - `Web Browser,"You are a Web Browser. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:24:- `src/huey/memory/PY/sync_pygpt_structure.py`:31 - `"""Return True if ``dst`` does not exist or contains a placeholder header."""`
src/huey/memory/MD/placeholder-occurrences.md:25:- `src/huey/memory/PY/sync_pygpt_structure.py`:50 - `"""Copy file or directory from src to dst if missing or placeholder."""`
src/huey/memory/MD/placeholder-occurrences.md:28:- `src/huey/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:29:- `src/huey/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:31:- `tests/test_placeholder.py`:3 - `from huey.pygpt_net.controller.config.placeholder import Placeholder`
src/huey/memory/PY/ai_processor.py:47:    (LLM) ΓÇô currently ``ollama`` or ``pygpt_net`` ΓÇô for semantic text
src/huey/memory/PY/ai_processor.py:82:            ("pygpt_net", self._init_pygpt_backend),
src/huey/memory/PY/ai_processor.py:126:    def _init_pygpt_backend(self) -> object | None:
src/huey/memory/PY/ai_processor.py:127:        """Return a ``pygpt_net`` client instance when possible."""
src/huey/memory/PY/ai_processor.py:129:        spec = importlib.util.find_spec("pygpt_net")
src/huey/memory/PY/ai_processor.py:133:        module = importlib.import_module("pygpt_net")
src/huey/memory/PY/ai_processor.py:253:        elif self._llm_backend == "pygpt_net":
src/huey/memory/PY/ai_tools_gui.py:153:    config = ConfigManager("config/pygpt_net/config.json")
src/huey/memory/PY/check_inter_program_connectivity.py:15:"""Verify that hueyos and pygpt_net modules import successfully."""
src/huey/memory/PY/check_inter_program_connectivity.py:21:    from .pygpt_integration import prepare_pygpt
src/huey/memory/PY/check_inter_program_connectivity.py:23:    from pygpt_integration import prepare_pygpt  # type: ignore
src/huey/memory/PY/check_inter_program_connectivity.py:33:    return prepare_pygpt()
src/huey/memory/PY/config_toggle_gui.py:32:DEFAULT_CONFIG = "config/pygpt_net/config.json"
src/huey/memory/PY/example_plugin.py:14:"""Minimal example plugin for the PyGPT application."""
src/huey/memory/PY/example_plugin.py:18:from pygpt_net.plugin.base.plugin import BasePlugin
src/huey/memory/PY/example_tool.py:14:"""Tiny custom tool usable with the PyGPT GUI."""
src/huey/memory/PY/example_tool.py:20:from pygpt_net.tools.base import BaseTool
src/huey/memory/PY/install_gui.py:29:DEFAULT_CONFIG_PATH = Path("config") / "pygpt_net" / "config.json"
src/huey/memory/PY/installer.py:158:            [sys.executable, "sync_pygpt_structure.py"],
src/huey/memory/PY/license_cli.py:19:DEFAULT_CONFIG = "config/pygpt_net/config.json"
src/huey/memory/PY/license_gui.py:50:def show_license_gui(config_path: str | Path = "config/pygpt_net/config.json") -> None:
src/huey/memory/PY/llm.py:6:"""Abstractions for interacting with LLM providers via the PyHuey/PyGPT-net stack."""
src/huey/memory/PY/llm.py:15:from huey.pygpt_integration import prepare_pygpt
src/huey/memory/PY/llm.py:41:        self._pygpt_agent: Any | None = None
src/huey/memory/PY/llm.py:42:        self._register_with_pygpt()
src/huey/memory/PY/llm.py:81:        """Load preset metadata from the pygpt configuration tree."""
src/huey/memory/PY/llm.py:83:        if not prepare_pygpt():
src/huey/memory/PY/llm.py:88:            resources.files("pygpt_net") / "data" / "config" / "presets" / preset_name
src/huey/memory/PY/llm.py:96:    def _register_with_pygpt(self) -> None:
src/huey/memory/PY/llm.py:97:        """Instantiate a pygpt agent wrapper for integration metadata."""
src/huey/memory/PY/llm.py:99:        if not prepare_pygpt():
src/huey/memory/PY/llm.py:100:            self._pygpt_agent = None
src/huey/memory/PY/llm.py:105:                from pygpt_net.provider.agents.openai import (
src/huey/memory/PY/llm.py:109:                from pygpt_net.provider.agents.react import ReactAgent as ProviderAgent
src/huey/memory/PY/llm.py:111:                from pygpt_net.provider.agents.planner import (
src/huey/memory/PY/llm.py:115:            self._pygpt_agent = None
src/huey/memory/PY/llm.py:119:            self._pygpt_agent = ProviderAgent()
src/huey/memory/PY/llm.py:121:            self._pygpt_agent = None
src/huey/memory/PY/preload_data.py:15:    prompts_file = BASE_DIR / "prompts" / "pygpt_prompts.csv"
src/huey/memory/PY/pygpt_custom_cli.py:4:# HueyOS: Pygpt Custom Cli module (huey)
src/huey/memory/PY/pygpt_custom_cli.py:13:from .pygpt_memory import Memory
src/huey/memory/PY/pygpt_custom_cli.py:16:class CustomPyGPT:
src/huey/memory/PY/pygpt_custom_cli.py:83:__all__ = ["CustomPyGPT"]
src/huey/memory/PY/pygpt_integration.py:1:"""Utility helpers for wiring PyHuey/PyGPT-net into Monkey Head.
src/huey/memory/PY/pygpt_integration.py:4:of ``pygpt_net``.  They are intentionally lightweight so they can be imported
src/huey/memory/PY/pygpt_integration.py:17:_PYGPT_PREPARED = False
src/huey/memory/PY/pygpt_integration.py:18:_PYGPT_ACTIVE_SOURCE: "PyHueySource | None" = None
src/huey/memory/PY/pygpt_integration.py:23:    """A possible source tree for the ``pygpt_net`` package."""
src/huey/memory/PY/pygpt_integration.py:74:        "pygpt-mhp": "vendor",
src/huey/memory/PY/pygpt_integration.py:86:    """Return ordered PyHuey/PyGPT-net source candidates."""
src/huey/memory/PY/pygpt_integration.py:93:            package_path=root / "src" / "huey" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:95:            description="Lightweight PyGPT-net compatibility package shipped with HueyOS.",
src/huey/memory/PY/pygpt_integration.py:100:            package_path=root / "integrations" / "pyhuey" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:106:            path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src",
src/huey/memory/PY/pygpt_integration.py:107:            package_path=root / "vendor" / "pygpt" / "pygpt-mhp" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:109:            description="Vendored lightweight pygpt-MHP mirror.",
src/huey/memory/PY/pygpt_integration.py:113:            path=root / "vendor" / "pygpt" / "py-gpt" / "src",
src/huey/memory/PY/pygpt_integration.py:114:            package_path=root / "vendor" / "pygpt" / "py-gpt" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:120:            path=root / "pygpt",
src/huey/memory/PY/pygpt_integration.py:121:            package_path=root / "pygpt" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:123:            description="Historical root-level PyGPT checkout.",
src/huey/memory/PY/pygpt_integration.py:127:            path=root / "pygpt" / "src",
src/huey/memory/PY/pygpt_integration.py:128:            package_path=root / "pygpt" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:130:            description="Historical root-level PyGPT src checkout.",
src/huey/memory/PY/pygpt_integration.py:134:            path=root / "repo" / "pygpt-MHP" / "src",
src/huey/memory/PY/pygpt_integration.py:135:            package_path=root / "repo" / "pygpt-MHP" / "src" / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:137:            description="Historical repo/pygpt-MHP checkout.",
src/huey/memory/PY/pygpt_integration.py:142:    env_value = os.environ.get("PYGPT_EXTRA_PATHS")
src/huey/memory/PY/pygpt_integration.py:154:                package_path=source_path / "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:156:                description="Operator-provided PyGPT-net source path.",
src/huey/memory/PY/pygpt_integration.py:174:    """Return ordered candidate directories that may house ``pygpt_net`` sources."""
src/huey/memory/PY/pygpt_integration.py:182:    """Return source candidates that currently contain ``pygpt_net``."""
src/huey/memory/PY/pygpt_integration.py:203:def prepare_pygpt(
src/huey/memory/PY/pygpt_integration.py:204:    module_name: str = "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:215:    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
src/huey/memory/PY/pygpt_integration.py:218:    if _PYGPT_PREPARED:
src/huey/memory/PY/pygpt_integration.py:222:        _PYGPT_PREPARED = True
src/huey/memory/PY/pygpt_integration.py:223:        _PYGPT_ACTIVE_SOURCE = None
src/huey/memory/PY/pygpt_integration.py:238:            _PYGPT_PREPARED = True
src/huey/memory/PY/pygpt_integration.py:239:            _PYGPT_ACTIVE_SOURCE = candidate
src/huey/memory/PY/pygpt_integration.py:246:    module_name: str = "pygpt_net",
src/huey/memory/PY/pygpt_integration.py:252:    prepared = prepare_pygpt(module_name, source=source)
src/huey/memory/PY/pygpt_integration.py:260:            _PYGPT_ACTIVE_SOURCE.as_dict()
src/huey/memory/PY/pygpt_integration.py:261:            if _PYGPT_ACTIVE_SOURCE
src/huey/memory/PY/pygpt_integration.py:268:def reset_pygpt_state() -> None:
src/huey/memory/PY/pygpt_integration.py:271:    global _PYGPT_ACTIVE_SOURCE, _PYGPT_PREPARED
src/huey/memory/PY/pygpt_integration.py:272:    _PYGPT_PREPARED = False
src/huey/memory/PY/pygpt_integration.py:273:    _PYGPT_ACTIVE_SOURCE = None
src/huey/memory/PY/pygpt_integration.py:281:    "prepare_pygpt",
src/huey/memory/PY/pygpt_integration.py:284:    "reset_pygpt_state",
src/huey/memory/PY/pygpt_memory.py:4:# HueyOS: Pygpt Memory module (huey)
src/huey/memory/PY/pygpt_memory.py:6:"""Simplified conversation memory helpers for Monkey Head's PyGPT integration."""
src/huey/memory/PY/pygpt_memory.py:12:    """A minimal conversation buffer compatible with the legacy PyGPT tooling."""
src/huey/memory/PY/resources.py:32:        os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "icons"
src/huey/memory/PY/resources.py:35:        os.path.dirname(__file__), "..", "src", "pygpt_net", "icons.qrc"
src/huey/memory/PY/resources.py:45:            "pygpt_net",
src/huey/memory/PY/resources.py:51:            os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "js", "katex"
src/huey/memory/PY/resources.py:55:        os.path.dirname(__file__), "..", "src", "pygpt_net", "js.qrc"
src/huey/memory/PY/resources.py:62:            os.path.dirname(__file__), "..", "src", "pygpt_net", "data", "js", "katex"
src/huey/memory/PY/resources.py:66:        os.path.dirname(__file__), "..", "src", "pygpt_net", "css.qrc"
src/huey/memory/PY/resources.py:76:            "pygpt_net",
src/huey/memory/PY/resources.py:84:        os.path.dirname(__file__), "..", "src", "pygpt_net", "fonts.qrc"
src/huey/memory/PY/run.py:19:from .pygpt_integration import prepare_pygpt, pyhuey_status
src/huey/memory/PY/run.py:26:    from .pygpt_custom_cli import CustomPyGPT
src/huey/memory/PY/run.py:28:    CustomPyGPT().run_cli()
src/huey/memory/PY/run.py:64:def _prepare_pygpt(source: str | None = None) -> bool:
src/huey/memory/PY/run.py:65:    """Ensure :mod:`pygpt_net` is importable either from site-packages or vendors."""
src/huey/memory/PY/run.py:67:    return prepare_pygpt(source=source)
src/huey/memory/PY/run.py:77:    if not _prepare_pygpt(source):
src/huey/memory/PY/run.py:81:        from pygpt_net.app import run as cli_run
src/huey/memory/PY/run.py:97:    if not _prepare_pygpt(source):
src/huey/memory/PY/run.py:98:        raise RuntimeError("pygpt_net package is not available")
src/huey/memory/PY/run.py:100:    from pygpt_net.app import run as pygpt_run
src/huey/memory/PY/run.py:102:    from huey.pygpt_net.tools.manager import MonkeyManager
src/huey/memory/PY/run.py:104:    pygpt_run(tools=[MonkeyManager()])
src/huey/memory/PY/run.py:173:        "--version", action="store_true", help="Print pygpt_net version and exit"
src/huey/memory/PY/run.py:184:        help="Select PyHuey/PyGPT-net source discovery preference",
src/huey/memory/PY/run.py:236:        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)
src/huey/memory/PY/run.py:237:    elif "PYGPT_WORKDIR" not in os.environ:
src/huey/memory/PY/run.py:238:        os.environ["PYGPT_WORKDIR"] = str(Path(__file__).resolve().parent.parent)
src/huey/memory/PY/run.py:296:        _prepare_pygpt(args.pyhuey_source)
src/huey/memory/PY/run.py:298:            from pygpt_net import __version__
src/huey/memory/PY/run.py:299:        except Exception:  # pragma: no cover - pygpt missing
src/huey/memory/PY/run.py:301:        print(f"pygpt_net version: {__version__}")
src/huey/memory/PY/set_api_keys.py:9:CONFIG_PATH = os.path.join("config", "pygpt_net", "config.json")
src/huey/memory/PY/setup.py:78:        "pygpt-net>=2.7.12",
src/huey/memory/PY/startup.py:71:        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)
src/huey/memory/PY/sync_pygpt_structure.py:4:# HueyOS: Sync Pygpt Structure module (huey/memory/PY)
src/huey/memory/PY/sync_pygpt_structure.py:14:"""Synchronize vendored pygpt-MHP files with the local project.
src/huey/memory/PY/sync_pygpt_structure.py:16:The script copies files from ``vendor/pygpt/pygpt-mhp`` into the main repository so
src/huey/memory/PY/sync_pygpt_structure.py:27:PYGPT_DIR = os.path.join("vendor", "pygpt", "pygpt-mhp")
src/huey/memory/PY/sync_pygpt_structure.py:76:        description="Copy files from the vendored pygpt-MHP mirror into the main project"
src/huey/memory/PY/sync_pygpt_structure.py:85:    mirror_tree(PYGPT_DIR, ROOT_DIR, depth=args.depth)
src/huey/memory/PY/update_prompts.py:10:INPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")
src/huey/memory/PY/update_prompts.py:11:OUTPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")  # overwrite
src/huey/memory/SH/build.sh:35:mv "$DIR_PARENT"/dist/Linux "$DIR_PARENT"/dist/pygpt-$VERSION
src/huey/memory/SH/build.sh:37:zip -r pygpt-$VERSION.zip pygpt-$VERSION -9
src/huey/memory/SH/build.sh:43:if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.zip" ]; then
src/huey/memory/SH/build.sh:44:        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.zip
src/huey/memory/SH/build.sh:47:if [ -f "$DIR_PARENT/dist/pygpt-$VERSION.msi" ]; then
src/huey/memory/SH/build.sh:48:        sha1sum "$DIR_PARENT"/dist/pygpt-$VERSION.msi
src/huey/memory/SH/clean.sh:14:Placeholder for `repo/pygpt-MHP/bin/clean.sh` from the pygpt-MHP repo.
src/huey/memory/SH/resources.sh:14:Placeholder for `repo/pygpt-MHP/bin/resources.sh` from the pygpt-MHP repo.
src/huey/memory/SH/snaprun.sh:43:python3 "$SNAP"/src/pygpt_net/app.py "$@"
src/huey/memory/SH/sort_locale.sh:14:Placeholder for `repo/pygpt-MHP/bin/sort_locale.sh` from the pygpt-MHP repo.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:241:* The software baseline is Debian 14 Forky, Python 3.13.x, PyGPT-net, and Ollama.
src/huey/memory/YAML/config.yaml:18:    - pygpt-MHP
src/huey/prompts/master-plan-v2-final.json:90:    "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v3.json:110:      "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v3.json:279:        "Run PyGPT-net and Ollama.",
src/huey/prompts/master-plan-v5.json:126:      "orchestrator": "PyGPT-net",
src/huey/prompts/master-plan-v5.json:343:        "Run PyGPT-net and Ollama.",
src/huey/pygpt_custom_cli.py:4:# HueyOS: PyGPT custom CLI compatibility wrapper (src)
src/huey/pygpt_custom_cli.py:6:"""Expose the maintained CustomPyGPT implementation under :mod:`huey`.
src/huey/pygpt_custom_cli.py:9:implementation in :mod:`huey.memory.PY.pygpt_custom_cli`.
src/huey/pygpt_custom_cli.py:14:from .memory.PY import pygpt_custom_cli as _pygpt_custom_cli
src/huey/pygpt_custom_cli.py:16:__all__ = list(getattr(_pygpt_custom_cli, "__all__", ()))
src/huey/pygpt_custom_cli.py:18:globals().update({name: getattr(_pygpt_custom_cli, name) for name in __all__})
src/huey/pygpt_integration.py:4:# HueyOS: PyGPT integration compatibility wrapper (src)
src/huey/pygpt_integration.py:6:"""Expose PyHuey/PyGPT integration utilities under :mod:`huey.pygpt_integration`."""
src/huey/pygpt_integration.py:10:from .memory.PY import pygpt_integration as _pygpt_integration
src/huey/pygpt_integration.py:12:__all__ = list(getattr(_pygpt_integration, "__all__", ()))
src/huey/pygpt_integration.py:14:globals().update({name: getattr(_pygpt_integration, name) for name in __all__})
src/huey/pygpt_memory.py:7:_impl = import_module("huey.memory.PY.pygpt_memory")
src/huey/pygpt_net/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net
src/huey/pygpt_net/__init__.py:6:"""Minimal stub of the :mod:`pygpt_net` package for integration tests."""
src/huey/pygpt_net/__init__.py:21:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
src/huey/pygpt_net/__init__.py:33:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
src/huey/pygpt_net/app.py:4:# HueyOS: App module (huey/pygpt_net)
src/huey/pygpt_net/app.py:14:    """Simulate launching the PyGPT GUI with the provided tools."""
src/huey/pygpt_net/controller/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/controller
src/huey/pygpt_net/controller/__init__.py:6:"""Controller shims for mirrored PyGPT configuration modules."""
src/huey/pygpt_net/controller/agent/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/controller/agent
src/huey/pygpt_net/controller/agent/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/common.py:6:# HueyOS: Common module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/common.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/common.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/common.py:17:from pygpt_net.core.types import MODE_AGENT
src/huey/pygpt_net/controller/agent/common.py:18:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/agent/experts.py:6:# HueyOS: Experts module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/experts.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/experts.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/experts.py:19:from pygpt_net.core.bridge import BridgeContext
src/huey/pygpt_net/controller/agent/experts.py:20:from pygpt_net.core.ctx.reply import ReplyContext
src/huey/pygpt_net/controller/agent/experts.py:21:from pygpt_net.core.events import KernelEvent, RenderEvent
src/huey/pygpt_net/controller/agent/experts.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_EXPERT
src/huey/pygpt_net/controller/agent/experts.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/legacy.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/legacy.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/legacy.py:19:from pygpt_net.core.bridge import BridgeContext
src/huey/pygpt_net/controller/agent/legacy.py:20:from pygpt_net.core.ctx.reply import ReplyContext
src/huey/pygpt_net/controller/agent/legacy.py:21:from pygpt_net.core.events import KernelEvent
src/huey/pygpt_net/controller/agent/legacy.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_AGENT_LLAMA
src/huey/pygpt_net/controller/agent/legacy.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/legacy.py:24:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/agent/llama.py:6:# HueyOS: Llama module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/llama.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/controller/agent/llama.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/controller/agent/llama.py:19:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/controller/agent/llama.py:20:from pygpt_net.core.events import KernelEvent
src/huey/pygpt_net/controller/agent/llama.py:21:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/controller/agent/llama.py:22:from pygpt_net.utils import trans
src/huey/pygpt_net/controller/config/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/controller/config
src/huey/pygpt_net/controller/config/__init__.py:6:"""Configuration helpers for the mirrored PyGPT controller."""
src/huey/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (huey/pygpt_net/controller/config)
src/huey/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
src/huey/pygpt_net/controller/config/placeholder.py:15:    """Provide minimal preset discovery compatible with PyGPT widgets."""
src/huey/pygpt_net/core/agents/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/core/agents
src/huey/pygpt_net/core/agents/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/legacy.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/legacy.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/legacy.py:19:from pygpt_net.core.types import (
src/huey/pygpt_net/core/agents/memory.py:6:# HueyOS: Memory module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/memory.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/memory.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/memory.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/observer/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/core/agents/observer
src/huey/pygpt_net/core/agents/observer/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/observer/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/observer/evaluation.py:6:# HueyOS: Evaluation module (huey/pygpt_net/core/agents/observer)
src/huey/pygpt_net/core/agents/observer/evaluation.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/observer/evaluation.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/observer/evaluation.py:20:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/core/agents/provider.py:6:# HueyOS: Provider module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/provider.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/provider.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/provider.py:19:from pygpt_net.provider.agents.base import BaseAgent
src/huey/pygpt_net/core/agents/runner.py:6:# HueyOS: Runner module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/runner.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/runner.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/runner.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/runner.py:21:from pygpt_net.core.bridge.worker import BridgeSignals
src/huey/pygpt_net/core/agents/runner.py:22:from pygpt_net.core.events import Event, KernelEvent
src/huey/pygpt_net/core/agents/runner.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/core/agents/runner.py:24:from pygpt_net.utils import trans
src/huey/pygpt_net/core/agents/tools.py:6:# HueyOS: Tools module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/tools.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/core/agents/tools.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/core/agents/tools.py:22:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/core/agents/tools.py:23:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/data/config/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
src/huey/pygpt_net/data/config/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
src/huey/pygpt_net/data/config/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
src/huey/pygpt_net/item/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/item
src/huey/pygpt_net/item/preset.py:4:# HueyOS: Preset module (huey/pygpt_net/item)
src/huey/pygpt_net/item/preset.py:16:    """Minimal representation of a PyGPT preset definition."""
src/huey/pygpt_net/plugin/agent/__init__.py:6:# HueyOS: Package initializer for huey/pygpt_net/plugin/agent
src/huey/pygpt_net/plugin/agent/__init__.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/plugin/agent/__init__.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/plugin/agent/__init__.py:17:from pygpt_net.core.events import Event
src/huey/pygpt_net/plugin/agent/__init__.py:18:from pygpt_net.item.ctx import CtxItem
src/huey/pygpt_net/plugin/agent/__init__.py:19:from pygpt_net.plugin.base.plugin import BasePlugin
src/huey/pygpt_net/plugin/agent/config.py:6:# HueyOS: Config module (huey/pygpt_net/plugin/agent)
src/huey/pygpt_net/plugin/agent/config.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/plugin/agent/config.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/plugin/agent/config.py:17:from pygpt_net.plugin.base.config import BaseConfig, BasePlugin
src/huey/pygpt_net/provider/agents/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/provider/agents
src/huey/pygpt_net/provider/agents/base.py:6:# HueyOS: Base module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/base.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/base.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai.py:6:# HueyOS: Openai module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/openai.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/openai.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai_assistant.py:6:# HueyOS: Openai Assistant module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/openai_assistant.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/openai_assistant.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/openai_assistant.py:20:from pygpt_net.core.bridge.context import BridgeContext
src/huey/pygpt_net/provider/agents/planner.py:6:# HueyOS: Planner module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/planner.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/planner.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/react.py:6:# HueyOS: React module (huey/pygpt_net/provider/agents)
src/huey/pygpt_net/provider/agents/react.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/provider/agents/react.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/provider/agents/react.py:21:from pygpt_net.core.types import MODE_VISION
src/huey/pygpt_net/tools/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/tools
src/huey/pygpt_net/tools/__init__.py:6:"""Tool shims that integrate Monkey Head with the PyGPT stub."""
src/huey/pygpt_net/tools/manager.py:4:# HueyOS: Manager module (huey/pygpt_net/tools)
src/huey/pygpt_net/tools/manager.py:6:"""Minimal Monkey Head manager tool for the PyGPT stub environment."""
src/huey/pygpt_net/tools/manager.py:14:    """Expose Monkey Head automation hooks inside the PyGPT GUI."""
src/huey/pygpt_net/tools/manager/__init__.py:4:# HueyOS: Package initializer for huey/pygpt_net/tools/manager
src/huey/pygpt_net/tools/manager/__init__.py:18:try:  # pragma: no cover - exercised when the full PyGPT UI is installed
src/huey/pygpt_net/tools/manager/__init__.py:19:    from pygpt_net.tools.base import BaseTool
src/huey/pygpt_net/tools/manager/__init__.py:30:try:  # pragma: no cover - exercised when the full PyGPT UI is installed
src/huey/pygpt_net/tools/manager/__init__.py:31:    from pygpt_net.utils import trans
src/huey/pygpt_net/tools/manager/__init__.py:78:    """Expose Monkey Head management tasks in the PyGPT UI."""
src/huey/pygpt_net/ui/layout/toolbox/agent.py:6:# HueyOS: Agent module (huey/pygpt_net/ui/layout/toolbox)
src/huey/pygpt_net/ui/layout/toolbox/agent.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/ui/layout/toolbox/agent.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/ui/layout/toolbox/agent.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
src/huey/pygpt_net/ui/layout/toolbox/agent.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
src/huey/pygpt_net/ui/layout/toolbox/agent.py:19:from pygpt_net.utils import trans
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:6:# HueyOS: Agent Llama module (huey/pygpt_net/ui/layout/toolbox)
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:9:# This file is a part of PYGPT package               #
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:10:# Website: https://pygpt.net                         #
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
src/huey/pygpt_net/ui/layout/toolbox/agent_llama.py:19:from pygpt_net.utils import trans
src/huey/pyhuey_integration.py:10:from .memory.PY import pygpt_integration as _pyhuey_integration
src/hueyos/cli/commands/runtime.py:53:        help="Use the lightweight CustomPyGPT CLI without GUI dependencies.",
src/hueyos/pygpt_custom_cli.py:1:"""Compatibility module exposing :mod:`huey.pygpt_custom_cli` under :mod:`hueyos`."""
src/hueyos/pygpt_custom_cli.py:5:from huey.pygpt_custom_cli import *  # noqa: F401,F403
tests/test_custom_pygpt_cli.py:4:# HueyOS: Test Custom Pygpt Cli module (tests)
tests/test_custom_pygpt_cli.py:6:from hueyos.pygpt_custom_cli import CustomPyGPT
tests/test_custom_pygpt_cli.py:10:    bot = CustomPyGPT()
tests/test_custom_pygpt_cli.py:17:    bot = CustomPyGPT(prompt_file=prompt_file)
tests/test_custom_pygpt_cli.py:21:def test_pygpt_wrappers_export_maintained_implementation():
tests/test_custom_pygpt_cli.py:22:    from huey.memory.PY.pygpt_custom_cli import CustomPyGPT as MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:23:    from huey.pygpt_custom_cli import CustomPyGPT as HueyCustomPyGPT
tests/test_custom_pygpt_cli.py:24:    from hueyos.pygpt_custom_cli import CustomPyGPT as HueyOSCustomPyGPT
tests/test_custom_pygpt_cli.py:26:    assert HueyCustomPyGPT is MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:27:    assert HueyOSCustomPyGPT is MaintainedCustomPyGPT
tests/test_custom_pygpt_cli.py:31:    bot = CustomPyGPT()
tests/test_load_cli.py:15:        if name.startswith("pygpt_net"):
tests/test_memory.py:16:from hueyos.pygpt_memory import Memory
tests/test_nltk_data_directory.py:9:from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state
tests/test_nltk_data_directory.py:17:    monkeypatch.setenv("PYGPT_NLTK_DATA_DIR", str(custom_dir))
tests/test_nltk_data_directory.py:18:    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)
tests/test_nltk_data_directory.py:20:    reset_pygpt_state()
tests/test_nltk_data_directory.py:21:    assert prepare_pygpt(source="package")
tests/test_nltk_data_directory.py:23:    module = importlib.import_module("pygpt_net")
tests/test_nltk_data_directory.py:28:        sys.modules["pygpt_net"] = module
tests/test_placeholder.py:3:from huey.pygpt_net.controller.config.placeholder import Placeholder
tests/test_pygpt_integration.py:6:from huey.pygpt_integration import (
tests/test_pygpt_integration.py:10:    prepare_pygpt,
tests/test_pygpt_integration.py:12:    reset_pygpt_state,
tests/test_pygpt_integration.py:20:    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(extra_dir))
tests/test_pygpt_integration.py:26:    assert root / "vendor" / "pygpt" / "pygpt-mhp" / "src" in paths
tests/test_pygpt_integration.py:38:def test_prepare_pygpt_uses_extra_paths(monkeypatch, tmp_path):
tests/test_pygpt_integration.py:40:    package_root = dummy_root / "pygpt_net"
tests/test_pygpt_integration.py:44:    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(dummy_root))
tests/test_pygpt_integration.py:46:    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)
tests/test_pygpt_integration.py:48:    reset_pygpt_state()
tests/test_pygpt_integration.py:49:    assert prepare_pygpt(source="extra")
tests/test_pygpt_integration.py:51:    import pygpt_net  # type: ignore
tests/test_pygpt_integration.py:53:    assert getattr(pygpt_net, "__version__", None) == "test-vendor"
tests/test_pygpt_integration.py:54:    reset_pygpt_state()
tests/test_pygpt_integration.py:58:    reset_pygpt_state()
tests/test_pygpt_integration.py:62:    assert status["module"] == "pygpt_net"
tests/test_pyhuey_manager.py:5:from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state
tests/test_pyhuey_manager.py:9:    reset_pygpt_state()
tests/test_pyhuey_manager.py:10:    assert prepare_pygpt(source="package")
tests/test_pyhuey_manager.py:12:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_pyhuey_manager.py:23:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_pyhuey_manager.py:40:    from huey.pygpt_net.tools.manager import MonkeyManager
tests/test_python_compatibility.py:31:def test_pygpt_marker_allows_python_313() -> None:
tests/test_python_compatibility.py:32:    line = _get_requirement_line("pygpt-net")
tests/test_run_minimal.py:8:from hueyos.pygpt_custom_cli import CustomPyGPT
tests/test_run_minimal.py:18:    monkeypatch.setattr(CustomPyGPT, "run_cli", fake_run)
vendor/pygpt/README.md:1:# PyGPT Vendor Mirrors
vendor/pygpt/README.md:3:This directory holds lightweight PyGPT/PyGPT-net mirrors used by HueyOS tests
vendor/pygpt/README.md:9:1. the packaged compatibility tree under `src/huey/pygpt_net`,
vendor/pygpt/py-gpt/README.md:1:# PyHuey / PyGPT vendor placeholder
vendor/pygpt/py-gpt/README.md:3:This directory emulates the upstream [`py-gpt`](https://github.com/szczyglis-dev/py-gpt) submodule used by Monkey Head. It contains a lightweight `pygpt_net` compatibility stub used during the PyHuey cockpit identity migration, so the project can run and test without fetching the full upstream repository.
vendor/pygpt/py-gpt/README.md:7:- Upstream package identity and compatibility are preserved via the `pygpt-net` project name and `pygpt` console script.
vendor/pygpt/py-gpt/README.md:8:- A `pyhuey` console script is also exposed, mapped to the same entrypoint as `pygpt`.
vendor/pygpt/py-gpt/README.md:9:- This stub preserves PyGPT provenance; it is not presented as a separate published `pyhuey` package.
vendor/pygpt/py-gpt/README.md:11:If you need the full implementation, replace this directory with the real submodule checkout or install `pygpt-net` from PyPI.
vendor/pygpt/py-gpt/pyproject.toml:6:name = "pygpt-net"
vendor/pygpt/py-gpt/pyproject.toml:8:description = "PyHuey cockpit fork compatibility stub derived from upstream PyGPT (published package name remains pygpt-net)."
vendor/pygpt/py-gpt/pyproject.toml:17:"Upstream PyGPT" = "https://github.com/szczyglis-dev/py-gpt"
vendor/pygpt/py-gpt/pyproject.toml:20:pygpt = "pygpt_net:main"
vendor/pygpt/py-gpt/pyproject.toml:21:pyhuey = "pygpt_net:main"
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:1:"""Minimal stub of the :mod:`pygpt_net` package for local development.
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:28:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:40:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:67:    """Compatibility CLI entrypoint for pygpt/pyhuey console scripts."""
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:69:    print("pygpt-net vendor stub is installed (Monkey-Head-Project / PyHuey compatibility mode).")
vendor/pygpt/pygpt-mhp/README.md:1:# pygpt-MHP
vendor/pygpt/pygpt-mhp/README.md:3:This directory vendors a lightweight mirror of the PyGPT-net integration used by the
vendor/pygpt/pygpt-mhp/README.md:5:(`pip install -e repo/pygpt-MHP`) without fetching the upstream repository when working
vendor/pygpt/pygpt-mhp/pyproject.toml:6:name = "pygpt-MHP"
vendor/pygpt/pygpt-mhp/pyproject.toml:8:description = "Monkey Head Project - PyGPT integration stubs"
vendor/pygpt/pygpt-mhp/setup.cfg:2:name = pygpt-MHP
vendor/pygpt/pygpt-mhp/setup.cfg:4:description = Monkey Head Project - PyGPT integration stubs
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:6:"""Minimal stub of the :mod:`pygpt_net` package for integration tests."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:21:_CUSTOM_ENV_VAR: Final[str] = "PYGPT_NLTK_DATA_DIR"
vendor/pygpt/pygpt-mhp/src/pygpt_net/__init__.py:33:            Path.home() / ".cache" / "pygpt_net" / "nltk_data",
vendor/pygpt/pygpt-mhp/src/pygpt_net/app.py:4:# HueyOS: App module (repo/pygpt-MHP/src/pygpt_net)
vendor/pygpt/pygpt-mhp/src/pygpt_net/app.py:14:    """Simulate launching the PyGPT GUI with the provided tools."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/__init__.py:6:"""Controller shims for mirrored PyGPT configuration modules."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller/agent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:6:# HueyOS: Common module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:17:from pygpt_net.core.types import MODE_AGENT
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:18:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:6:# HueyOS: Experts module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:19:from pygpt_net.core.bridge import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:20:from pygpt_net.core.ctx.reply import ReplyContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:21:from pygpt_net.core.events import KernelEvent, RenderEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_EXPERT
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:19:from pygpt_net.core.bridge import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:20:from pygpt_net.core.ctx.reply import ReplyContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:21:from pygpt_net.core.events import KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:22:from pygpt_net.core.types import MODE_AGENT, MODE_AGENT_LLAMA
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:24:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:6:# HueyOS: Llama module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:19:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:20:from pygpt_net.core.events import KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:21:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/llama.py:22:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/controller/config
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py:6:"""Configuration helpers for the mirrored PyGPT controller."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (repo/pygpt-MHP/src/pygpt_net/controller/config)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:14:    """Provide minimal preset discovery compatible with PyGPT widgets."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/core/agents
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:19:from pygpt_net.core.types import (
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:6:# HueyOS: Memory module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/core/agents/observer
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:6:# HueyOS: Evaluation module (repo/pygpt-MHP/src/pygpt_net/core/agents/observer)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/observer/evaluation.py:20:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:6:# HueyOS: Provider module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/provider.py:19:from pygpt_net.provider.agents.base import BaseAgent
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:6:# HueyOS: Runner module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:21:from pygpt_net.core.bridge.worker import BridgeSignals
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:22:from pygpt_net.core.events import Event, KernelEvent
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/runner.py:24:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:6:# HueyOS: Tools module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:22:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/tools.py:23:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1249:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#vector-stores",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1432:        "urls": "https://pygpt.readthedocs.io/en/latest/configuration.html#data-loaders",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1762:            "List of commands": "https://pygpt.readthedocs.io/en/latest/accessibility.html"
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/item
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py:4:# HueyOS: Preset module (repo/pygpt-MHP/src/pygpt_net/item)
vendor/pygpt/pygpt-mhp/src/pygpt_net/item/preset.py:16:    """Minimal representation of a PyGPT preset definition."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:6:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/plugin/agent
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:17:from pygpt_net.core.events import Event
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:18:from pygpt_net.item.ctx import CtxItem
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:19:from pygpt_net.plugin.base.plugin import BasePlugin
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:6:# HueyOS: Config module (repo/pygpt-MHP/src/pygpt_net/plugin/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/config.py:17:from pygpt_net.plugin.base.config import BaseConfig, BasePlugin
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/provider/agents
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:6:# HueyOS: Base module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/base.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:6:# HueyOS: Openai module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:6:# HueyOS: Openai Assistant module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/openai_assistant.py:20:from pygpt_net.core.bridge.context import BridgeContext
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:6:# HueyOS: Planner module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/planner.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:6:# HueyOS: React module (repo/pygpt-MHP/src/pygpt_net/provider/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/provider/agents/react.py:21:from pygpt_net.core.types import MODE_VISION
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/tools
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/__init__.py:6:"""Tool shims that integrate Monkey Head with the PyGPT stub."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:4:# HueyOS: Manager module (repo/pygpt-MHP/src/pygpt_net/tools)
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:6:"""Minimal Monkey Head manager tool for the PyGPT stub environment."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager.py:14:    """Expose Monkey Head automation hooks inside the PyGPT GUI."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:4:# HueyOS: Package initializer for repo/pygpt-MHP/src/pygpt_net/tools/manager
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:13:from pygpt_net.tools.base import BaseTool
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:14:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/tools/manager/__init__.py:21:    """Expose Monkey Head management tasks in the PyGPT UI."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:6:# HueyOS: Agent module (repo/pygpt-MHP/src/pygpt_net/ui/layout/toolbox)
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:19:from pygpt_net.utils import trans
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:6:# HueyOS: Agent Llama module (repo/pygpt-MHP/src/pygpt_net/ui/layout/toolbox)
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:9:# This file is a part of PYGPT package               #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:10:# Website: https://pygpt.net                         #
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:17:from pygpt_net.ui.widget.option.slider import OptionSlider
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:18:from pygpt_net.ui.widget.option.toggle_label import ToggleLabel
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent_llama.py:19:from pygpt_net.utils import trans

## legacy

.migration/inventory/git-ls-files.pass-01.txt:91:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:96:integrations/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:293:platform/boot/grub/grub/x86_64-efi/legacy_password_test.mod
.migration/inventory/git-ls-files.pass-01.txt:294:platform/boot/grub/grub/x86_64-efi/legacycfg.mod
.migration/inventory/git-ls-files.pass-01.txt:442:platform/boot/legacy/isolinux/boot.cat
.migration/inventory/git-ls-files.pass-01.txt:443:platform/boot/legacy/isolinux/hdt.c32
.migration/inventory/git-ls-files.pass-01.txt:444:platform/boot/legacy/isolinux/install.cfg
.migration/inventory/git-ls-files.pass-01.txt:445:platform/boot/legacy/isolinux/isolinux.bin
.migration/inventory/git-ls-files.pass-01.txt:446:platform/boot/legacy/isolinux/isolinux.cfg
.migration/inventory/git-ls-files.pass-01.txt:447:platform/boot/legacy/isolinux/ldlinux.c32
.migration/inventory/git-ls-files.pass-01.txt:448:platform/boot/legacy/isolinux/libcom32.c32
.migration/inventory/git-ls-files.pass-01.txt:449:platform/boot/legacy/isolinux/libgpl.c32
.migration/inventory/git-ls-files.pass-01.txt:450:platform/boot/legacy/isolinux/libmenu.c32
.migration/inventory/git-ls-files.pass-01.txt:451:platform/boot/legacy/isolinux/libutil.c32
.migration/inventory/git-ls-files.pass-01.txt:452:platform/boot/legacy/isolinux/live.cfg
.migration/inventory/git-ls-files.pass-01.txt:453:platform/boot/legacy/isolinux/menu.cfg
.migration/inventory/git-ls-files.pass-01.txt:454:platform/boot/legacy/isolinux/splash.png
.migration/inventory/git-ls-files.pass-01.txt:455:platform/boot/legacy/isolinux/stdmenu.cfg
.migration/inventory/git-ls-files.pass-01.txt:456:platform/boot/legacy/isolinux/utilities.cfg
.migration/inventory/git-ls-files.pass-01.txt:457:platform/boot/legacy/isolinux/vesamenu.c32
.migration/inventory/git-ls-files.pass-01.txt:458:platform/boot/legacy/live/filesystem.packages
.migration/inventory/git-ls-files.pass-01.txt:459:platform/boot/legacy/live/filesystem.packages-remove
.migration/inventory/git-ls-files.pass-01.txt:460:platform/boot/legacy/live/vmlinuz
.migration/inventory/git-ls-files.pass-01.txt:461:platform/boot/legacy/live/vmlinuz-6.18.5-hueyos
.migration/inventory/git-ls-files.pass-01.txt:516:platform/packaging/firmware/dep11/firmware-b43legacy-installer.component
.migration/inventory/git-ls-files.pass-01.txt:517:platform/packaging/firmware/dep11/firmware-b43legacy-installer.patterns
.migration/inventory/git-ls-files.pass-01.txt:794:platform/packaging/pool/contrib/b/b43-fwcutter/firmware-b43legacy-installer_1%3a019-14_all.deb
.migration/inventory/git-ls-files.pass-01.txt:845:src/hueyos/legacy/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:846:src/hueyos/legacy/connectors.py
.migration/inventory/git-ls-files.pass-01.txt:905:src/huey/legacy/__init__.py
.migration/inventory/git-ls-files.pass-01.txt:906:src/huey/legacy/connectors.py
.migration/inventory/git-ls-files.pass-01.txt:1025:src/huey/memory/PDF/8 - MPH-VIC-20 C64 C128 [Integrated Legacy Hardware].pdf
.migration/inventory/git-ls-files.pass-01.txt:1061:src/huey/memory/PDF/Legacy Tech in 2025_ Floppy Disks, Zip Drives, and Vintage Ports.pdf
.migration/inventory/git-ls-files.pass-01.txt:1084:src/huey/memory/PDF/The MOS Technology VIC-II_ Architecture, Specifications, and Legacy.pdf
.migration/inventory/git-ls-files.pass-01.txt:1256:src/huey/memory/TXT/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt
.migration/inventory/git-ls-files.pass-01.txt:1298:src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt
.migration/inventory/git-ls-files.pass-01.txt:1327:src/huey/prompts/PAGES/Monkey_Head_Project_Page25_Legacy.pdf
.migration/inventory/git-ls-files.pass-01.txt:1354:src/huey/pygpt_net/controller/agent/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1359:src/huey/pygpt_net/core/agents/legacy.py
.migration/inventory/git-ls-files.pass-01.txt:1463:tests/test_legacy_connectors.py
.security/bandit-baseline.json:642:    "src/huey/legacy/__init__.py": {
.security/bandit-baseline.json:655:    "src/huey/legacy/connectors.py": {
.security/bandit-baseline.json:2358:    "src/huey/pygpt_net/controller/agent/legacy.py": {
.security/bandit-baseline.json:2423:    "src/huey/pygpt_net/core/agents/legacy.py": {
README.md:969:| `archives/` | Frozen payloads, snapshots, legacy material |
README.md:1121:| **Huey Core** | Legacy/previous name for the active proof body; replaced by the Brain/Body distinction. |
SECURITY.md:61:  * Debian ΓÇ£TrixieΓÇ¥ ΓÇö **historical/migration-only** compatibility target for legacy nodes.
docs/_build/html/_sources/development/v101.1-namespace-migration.md.txt:7:- `src/huey/memory/PY` is the legacy implementation surface until code is explicitly moved.
docs/_build/html/development/v101.1-namespace-migration.html:42:<li><p><code class="docutils literal notranslate"><span class="pre">src/huey/memory/PY</span></code> is the legacy implementation surface until code is explicitly moved.</p></li>
docs/audits/v101.1-pyhuey-branding-string-audit.md:25:- Additional user-facing references in optional installer scripts and legacy/deferred docs that still print "PyGPT/PyGPT-net" where PyHuey wording may be more appropriate.
docs/audits/v101.1-pyhuey-branding-string-audit.md:26:- Vendored/compatibility tree wording under legacy `pygpt_*` filenames that should be reviewed only when import compatibility is formally migrated.
docs/development/v101.1-namespace-migration.md:7:- `src/huey/memory/PY` is the legacy implementation surface until code is explicitly moved.
docs/kernel/kernel-6.18.2-runbook.md:1:# Historical Note: Linux 6.18.2 Migration (Legacy)
docs/kernel/kernel-6.18.2-runbook.md:3:> **Status:** Legacy documentation for a completed migration.
docs/kernel/kernel-6.18.2-runbook.md:31:For 7.0-era systems, this legacy migration should be interpreted as:
docs/kernel/kernel-6.18.2-runbook.md:42:## Legacy markers to watch for
docs/releases/2025-10-31-changeover.md:31:2. Move systems targeting legacy baseline language to the active 7.0 policy track.
docs/security/security-concerns-and-fixes.md:68:5. **Many legacy management helpers perform powerful host/container actions**
docs/unsorted/index.md:16:- [Linux 6.18.2 migration runbook (legacy archive)](kernel-6.18.2-runbook.md)
docs/unsorted/kernel-upgrade-phase2.md:4:It replaces old pre-7.0 migration notes and removes legacy references
docs/unsorted/kernel-upgrade-phase2.md:73:## Terminology and Legacy Status
docs/unsorted/kernel-validation-checklist.md:8:- [ ] Run `python scripts/check_stale_platform_strings.py` and verify no new stale strings were added outside approved legacy/archive paths.
docs/unsorted/kernel-validation-checklist.md:9:- [ ] If historical references are necessary, store them only in approved legacy/archive paths and label them as historical context.
docs/unsorted/kernel-validation-checklist.md:33:- [ ] Keep legacy migration notes in historical docs only.
docs/unsorted/repository-restructure-inventory.md:10:- `isolinux/` + `live/` ΓåÆ `platform/boot/legacy/`
docs/unsorted/repository-restructure-inventory.md:27:- `src/huey/prompts/OLD/` ΓåÆ `archives/prompts/legacy/`
docs/unsorted/repository-restructure-recommendation.md:72:- **Phase 3:** Archive legacy snapshots and remove temporary shims.
docs/unsorted/version-reference-classification.md:11:- **6.18.2-era content is legacy, compatibility-fixture, or immutable artifact context only**.
docs/unsorted/version-reference-classification.md:21:### Legacy archive
docs/unsorted/version-reference-classification.md:23:Historical migration notes kept for provenance and post-mortem context. Legacy
docs/unsorted/version-reference-classification.md:46:| `docs/index.md` | Active index + legacy pointer | Keep the 7.0 Phase 2 runbook as active and label 6.18.2 runbook as legacy archive. |
docs/unsorted/version-reference-classification.md:47:| `docs/kernel-6.18.2-runbook.md` | Legacy archive | Preserve as historical migration note only. |
docs/unsorted/version-reference-classification.md:60:  **legacy archive**, **historical context in active docs**, **test fixtures**,
docs/unsorted/version-reference-classification.md:69:   clear legacy label.
master-plan-v101.1.json:18:    "v8.0 + legacy constitution bundle",
master-plan-v101.1.json:574:      "legacy_name": "Huey Core",
master-plan-v101.1.json:1498:        "legacy_future_names": [
master-plan-v101.1.json:1797:      "role": "Dedicated portal terminal and artifact-grade doorway into Huey. It may be realized as a physical legacy computer or as a VM guest, but in both forms it remains lab infrastructure rather than Huey itself.",
master-plan-v101.1.json:1807:        "expansion_policy": "Do not add hardware merely because the chassis permits it; extra legacy hardware belongs to lab experiments unless it directly serves the portal role.",
master-plan-v101.1.json:1824:        "lab_validation": "Alternative drives, alternate operating systems such as Vista or XP x64, legacy peripherals, and different host setups may be used for lab-side testing, but those experiments do not become canonical Huey portal doctrine automatically."
master-plan-v101.1.json:1834:        "bring_up_note": "The currently observed BIOS-level validation belongs to the legacy hardware path. The Longhorn 4074 portal doctrine may continue on that hardware if feasible or in a VM if the hardware path becomes impractical."
master-plan-v101.1.json:1877:        "physical_state": "May be a physical legacy appliance or a VM guest.",
master-plan-v101.1.json:1893:      "huey_core_legacy": {
master-plan-v101.1.json:1898:        "status": "legacy name retained for continuity; replaced by Huey Body in active V31.0 language"
master-plan-v101.1.json:2275:      "Extended training material and open questions to include Vista Box firmware, drivers, install posture, and legacy-peripheral boundary work."
master-plan-v101.1.json:2282:      "Clarified that Huey Vista Box is a role first and may be embodied either as a physical legacy appliance or as a tightly controlled VM guest without changing its doctrinal job.",
master-plan-v101.1.json:2380:    "Do not call Huey Body 'Huey Core' except when discussing legacy documents or the rename.",
master-plan-v101.1.json:2544:    "allowed_legacy_context": "Older version labels may remain only inside archives, historical compiled_from_versions lists, transcripts, and provenance notes.",
master-plan-v101.1.json:2592:      "Windows 10 Pro": "fallback, legacy compatibility, and WSL experiment host",
master-plan-v101.1.json:2680:    "allowed_legacy_context": "Older version labels may remain only inside archives, historical compiled_from_versions lists, transcripts, changelogs, release-pass notes, and provenance notes.",
platform/boot/grub/grub/x86_64-efi/command.lst:98:extract_legacy_entries_configfile: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:99:extract_legacy_entries_source: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:117:legacy_check_password: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:118:legacy_configfile: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:119:legacy_initrd: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:120:legacy_initrd_nounzip: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:121:legacy_kernel: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:122:legacy_password: legacycfg
platform/boot/grub/grub/x86_64-efi/command.lst:123:legacy_source: legacycfg
platform/boot/grub/grub/x86_64-efi/moddep.lst:98:legacy_password_test: functional_test legacycfg
platform/boot/grub/grub/x86_64-efi/moddep.lst:273:legacycfg: crypto gcry_md5 normal password
platform/boot/legacy/live/filesystem.packages:110:firmware-b43legacy-installer	1:019-14
platform/boot/legacy/live/filesystem.packages:1123:openssl-provider-legacy	3.5.4-1+b1
platform/boot/legacy/live/filesystem.packages:1324:xserver-xorg-legacy	2:21.1.21-1
platform/installers/debian/Debian/install-deb.sh:243:        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_trixie.py"  # migration-only fallback for legacy nodes
platform/installers/debian/Debian/update-deb.sh:171:        "$project_root/huey/memory/PY/update_sources_to_trixie.py"  # migration-only fallback for legacy nodes
platform/packaging/dists/forky/contrib/binary-amd64/Packages:20: It is used by the firmware-b43(legacy)-installer packages as part of
platform/packaging/dists/forky/contrib/binary-amd64/Packages:62:Package: firmware-b43legacy-installer
platform/packaging/dists/forky/contrib/binary-amd64/Packages:71:Filename: pool/contrib/b/b43-fwcutter/firmware-b43legacy-installer_1%3a019-14_all.deb
platform/packaging/dists/forky/contrib/binary-amd64/Packages:78:Description: firmware installer for the b43legacy driver
platform/packaging/dists/forky/contrib/binary-amd64/Packages:79: This package downloads and installs the firmware needed by the b43legacy
platform/packaging/dists/forky/main/binary-amd64/Packages:1012:Conflicts: elilo, grub, grub-coreboot, grub-efi-ia32, grub-ieee1275, grub-legacy, grub-pc, grub-xen
platform/packaging/dists/forky/main/binary-amd64/Packages:1013:Replaces: grub, grub-coreboot, grub-efi-ia32, grub-ieee1275, grub-legacy, grub-pc, grub2 (<< 2.14~git20250718.0e36779-2)
platform/packaging/dists/forky/main/binary-amd64/Packages:1107:Breaks: grub-legacy (<< 0.97-84~)
platform/packaging/dists/forky/main/binary-amd64/Packages:1108:Replaces: grub, grub-coreboot, grub-efi-amd64, grub-efi-ia32, grub-ieee1275, grub-legacy, grub2 (<< 2.14~git20250718.0e36779-2)
platform/packaging/dists/forky/main/binary-amd64/Packages:1147:Breaks: grub-common (<< 2.14~), grub-legacy (<< 0.97-83~)
platform/packaging/dists/forky/main/binary-amd64/Packages:1148:Replaces: grub, grub-common, grub-legacy
platform/packaging/dists/forky/main/binary-amd64/Packages:1159: Legacy if installed on the same system.
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:2825: libmtdev is a library for translating evdev multitouch events using the legacy
platform/packaging/firmware/Contents-firmware:1027:/usr/lib/firmware/b43legacy/.placeholder                firmware-b43legacy-installer_1%3a019-14_all.deb contrib
scripts/check_canon_terms.py:18:    "legacy",
scripts/check_canon_terms.py:31:    "legacy",
scripts/check_stale_platform_strings.py:108:        print("Stale platform string check failed. Move these references to approved legacy/archive paths:")
src/huey/__init__.py:6:"""Compatibility package exposing the legacy Huey modules under ``src``."""
src/huey/__init__.py:30:_LEGACY_PREFIX = f"{__name__}.memory.PY"
src/huey/__init__.py:34:    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""
src/huey/__init__.py:40:            module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
src/huey/ai_processor.py:1:# Auto-generated bridge to legacy module
src/huey/api.py:14:# module object via ``sys.modules``; instead re-export legacy symbols explicitly.
src/huey/api.py:23:    """Delegate unknown attributes to the legacy API module for compatibility."""
src/huey/chapter_splitter.py:1:# Auto-generated bridge to legacy module
src/huey/cli.py:23:    """Parse CLI arguments for the legacy Huey entry point."""
src/huey/cli.py:40:    """Compatibility shim for legacy CLI entry points."""
src/huey/cli.py:43:        "The legacy CLI entry point is not available in this environment."
src/huey/cli.py:48:    """Invoke the legacy CLI with parsed arguments."""
src/huey/convert_png_to_jpeg.py:1:# Auto-generated bridge to legacy module
src/huey/core/system_checks.py:45:    behaviour without needing to modify the legacy implementation directly.
src/huey/error_handler.py:1:# Auto-generated bridge to legacy module
src/huey/file_manager.py:1:# Auto-generated bridge to legacy module
src/huey/huey_checks.py:1:# Auto-generated bridge to legacy module
src/huey/huey_core.py:1:# Auto-generated bridge to legacy module
src/huey/huey_disk_manager_temp.py:1:# Auto-generated bridge to legacy module
src/huey/huey_linux.py:1:# Auto-generated bridge to legacy module
src/huey/huey_remover.py:1:# Auto-generated bridge to legacy module
src/huey/huey_tkinter.py:1:# Auto-generated bridge to legacy module
src/huey/install_gui.py:1:# Auto-generated bridge to legacy module
src/huey/legacy/__init__.py:4:# HueyOS: Package initializer for huey/legacy
src/huey/legacy/__init__.py:6:"""Legacy hardware integration helpers for HueyOS."""
src/huey/legacy/__init__.py:9:    EmulatedLegacyConnector,
src/huey/legacy/__init__.py:10:    LegacyConnector,
src/huey/legacy/__init__.py:11:    LegacyConnectorFactory,
src/huey/legacy/__init__.py:12:    SerialLegacyConnector,
src/huey/legacy/__init__.py:16:    "EmulatedLegacyConnector",
src/huey/legacy/__init__.py:17:    "LegacyConnector",
src/huey/legacy/__init__.py:18:    "LegacyConnectorFactory",
src/huey/legacy/__init__.py:19:    "SerialLegacyConnector",
src/huey/legacy/connectors.py:4:# HueyOS: Connectors module (huey/legacy)
src/huey/legacy/connectors.py:6:"""Legacy system connector abstractions.
src/huey/legacy/connectors.py:34:class LegacyConnector(Protocol):
src/huey/legacy/connectors.py:35:    """Abstract interface implemented by all legacy connectors."""
src/huey/legacy/connectors.py:38:        """Establish the connection to the legacy system."""
src/huey/legacy/connectors.py:41:        """Send raw bytes to the legacy system."""
src/huey/legacy/connectors.py:44:        """Receive bytes from the legacy system."""
src/huey/legacy/connectors.py:51:class SerialLegacyConnector:
src/huey/legacy/connectors.py:62:                "pyserial is required for SerialLegacyConnector but is not installed"
src/huey/legacy/connectors.py:64:        LOGGER.info("Opening serial connection to legacy system on %s", self.port)
src/huey/legacy/connectors.py:71:        LOGGER.debug("Writing %s bytes to legacy serial device", len(payload))
src/huey/legacy/connectors.py:91:class EmulatedLegacyConnector:
src/huey/legacy/connectors.py:102:        LOGGER.info("Initialising emulated legacy connector")
src/huey/legacy/connectors.py:124:class LegacyConnectorFactory:
src/huey/legacy/connectors.py:128:    def create(config: Dict[str, Any]) -> LegacyConnector:
src/huey/legacy/connectors.py:131:            return SerialLegacyConnector(
src/huey/legacy/connectors.py:137:            return EmulatedLegacyConnector()
src/huey/legacy/connectors.py:138:        raise ValueError(f"Unsupported legacy connector mode: {mode}")
src/huey/license_cli.py:1:# Auto-generated bridge to legacy module
src/huey/license_gui.py:1:# Auto-generated bridge to legacy module
src/huey/log.py:1:# Auto-generated bridge to legacy module
src/huey/logging_setup.py:1:# Auto-generated bridge to legacy module
src/huey/memory/ARCHIVE/1) Monkey Head Project [Thesis].txt:23:- **Legacy Hardware Integration**: Incorporating platforms like the **Commodore VIC-20, C64, and C128** not only preserves historical computing insights but also illustrates how **older devices** can be revitalized through modern architectures, supporting both educational and practical objectives.
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:11:Inspired by themes of **grandeur**, **ambition**, and **legacy**, ΓÇ£OzymandiasΓÇ¥ symbolizes both the power of human achievement and the inevitability of decline. This duality informs the **Monkey Head Project**, underscoring that genuine innovation demands ambition moderated by humility.
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:54:Compatibility hurdlesΓÇöparticularly between **legacy** and **state-of-the-art** hardwareΓÇöhave largely been overcome, creating a **rich**, **interconnected** environment uniting historical contexts, computational strength, and modern data processing.
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:71:The poemΓÇÖs reminder of **impermanence** calls the Project to aim not only for near-term success but also a **sustained, far-reaching legacy**. As the Project advances, it must resist complacency, instead seeking **lasting impact** beyond ephemeral achievements.
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:82:In the spirit of *Ozymandias*, the Project remembers that **ambition** demands **continuous** effort, **adaptive** thinking, and **ethical** grounding. True success transcends technical triumphΓÇöit must also reflect **resilience**, **flexibility**, and principled innovation. By persistently evolving under these guiding values, the Monkey Head Project aspires to establish a legacy that withstands the erosion of time, forging an enduring contribution to **robotics** and **AI**.
src/huey/memory/ARCHIVE/20) Final Chapter [The Future].txt:81:By merging **ambition** with **rigorous methodology**, **ethical oversight**, and a **communal ethos**, the Monkey Head Project aspires to more than technical success. It aims to pioneer a **culture** of exploration and shared growth, standing on the legacy of landmark technologiesΓÇöfrom *legacy Commodore hardware* to **Huey**ΓÇöto forge bold new paths in the collective scientific imagination.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:78:#### 6.4 Watt (Apollo): The Luminary of Legacy
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:79:- In the vein of Apollo, the deity of prophecy and the arts, Watt presides over the Federation's cultural and creative initiatives. As a beacon of inspiration and scientific advancement, Watt nurtures a legacy enriched with artistic and intellectual pursuits, guiding the Federation towards a future where creativity and innovation flourish in harmony.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:27:A curated suite of Apple devices supports **development**, **deployment**, and **legacy integration** within the Command Center:
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:31:- **MacBook Pro (2012)**: Designated the ΓÇ£Transmitter,ΓÇ¥ ensuring backward compatibility with legacy systems and acting as a **bridge** between modern innovations and older peripherals.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:8:Within the Monkey Head Project, the **MacBook Pro 2012** (non-Retina) serves as the **ΓÇ£Transmitter,ΓÇ¥** specializing in interactions with legacy hardware and software. Despite its age, this MacBookΓÇÖs adaptability and rich connectivity options make it vital for bridging older systems and the ProjectΓÇÖs cutting-edge developments, ensuring **broad compatibility** and **inclusivity**.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:16:   - Though not state-of-the-art, it meets the ProjectΓÇÖs needs for reliable operation of legacy applications and essential tasks.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:24:   - **Intel HD Graphics 4000**, sufficient for basic graphical tasks and interfacing with legacy software requiring minimal GPU resources.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:34:#### 1. Legacy System Compatibility Testing
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:37:- **Legacy Software Suites**: Runs performance checks to confirm new Project features operate smoothly on older systems (VIC-20, C64, C128, etc.).  
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:43:- **Peripheral Integration**: Links legacy audio interfaces, external drives, and diagnostic equipment to newer systems, facilitating data transfer and persistent operational capabilities.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:70:By maintaining this connection between emerging tech and legacy hardware, the **MacBook Pro 2012** ensures the Monkey Head ProjectΓÇÖs innovations reach a larger, more diverse user base.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:75:**Backward compatibility** with older devices enables widespread adoption of the ProjectΓÇÖs AI and robotics solutions, spanning high-end laboratories and legacy-focused facilities alike.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:82:Acting as the **Transmitter**, the **MacBook Pro 2012** is indispensable to the Monkey Head Project, ensuring new advancements remain compatible with **past technologies**. Its specialized role in **legacy compatibility testing**, **communication bridging**, and **dual-boot** operation exemplifies the ProjectΓÇÖs commitment to **inclusivity** and **broader technological reach**. By unifying past and present, the MacBook Pro 2012 upholds the ProjectΓÇÖs foundational ethosΓÇömaking **cutting-edge** robotics and AI accessible to **all**.
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:34:   - **Middleware Interfaces**: Bridges new and legacy systems, ensuring older components remain interoperable with modern frameworks without compromising stability or flexibility.
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:1:Below is a **refined, cohesive** version of your text on integrating the **VIC-20**, **Commodore 64**, and **Commodore 128** within the **Monkey Head Project**ΓÇÖs Huey AI/OS. It retains the original structure and details, clarifying the importance, technical steps, and future directions of this legacy integration.
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:5:## VIC-20, C64, C128: Integrated Legacy Hardware
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:15:   - **Preservation & Education**: The VIC-20, C64, and C128 remain influential milestones in computing history. HueyΓÇÖs seamless operation on these devices honors their legacy, offering hands-on educational experiences that illustrate how programming languages and architectures have evolved.  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:18:2. **Legacy Compatibility**  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:28:   - **VICE Emulator**: Offers full system emulation, bridging legacy architectures with HueyΓÇÖs AI environment for real-time data exchange alongside contemporary components.
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:47:   - **Prototyping & Testing**: Legacy architecture forces developers to refine code structure, verifying that solutions remain lean and efficient.  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:63:   - **Collaborative Creativity**: Community events focus on creating or repurposing applications for these legacy systems, now augmented by HueyΓÇÖs modern features.  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:70:1. **Expansion of Legacy Support**  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:80:The integration of **VIC-20**, **Commodore 64**, and **C128** into the Monkey Head Project is far more than nostalgic preservation; it exemplifies how **classic systems** remain valuable within a **cutting-edge AI/OS** framework like **Huey**. By revitalizing legacy machines through **modern connectivity**, **expanded memory**, and **innovative software enhancements**, the Project breathes new life into historical computing platformsΓÇödemonstrating the trajectory from early microprocessors to sophisticated, adaptive AI. This initiative not only preserves computing heritage but enriches the modern landscape with insights, educational value, and ever-evolving community engagement.
src/huey/memory/JSON/PyGPT_Change_Log.json:247:        "Added instruction to model about mapped data directory in both legacy and IPython code interpreter.",
src/huey/memory/JSON/modes.json:70:            "name": "Agent (legacy)",
src/huey/memory/JSON/settings.json:251:            {"legacy": "Legacy (markdown)"}
src/huey/memory/MD/HARDWARE.md:16:> Any 6.18.2 references in this guide are legacy context markers only, not implementation targets.
src/huey/memory/MD/New-To-AI.md:3:The Monkey Head Project aims to build an adaptive AI Operating System (AIOS) called **Huey**, which coordinates robotics hardware and legacy systems. The project envisions a universally accessible platform that enhances human-machine collaboration and ensures ethical governance.
src/huey/memory/MD/New-To-AI.md:11:The project believes that with enough dedication, an individual can create a fully autonomous robot. Huey is designed to run on diverse hardware, from legacy machines like the VIC-20 and C64 to modern platforms.
src/huey/memory/MD/New-To-AI.md:13:**Phase 1 (April 11, 2024)** established foundational hardware and initial AI/OS integration, proving compatibility with legacy systems.
src/huey/memory/MD/New-To-AI.md:21:## Legacy Systems
src/huey/memory/MD/New-To-AI.md:22:Legacy machines such as **C64, VIC-20 and C128** are used for interfacing experiments, showcasing Huey's adaptability and proving that modern AI can breathe new life into old technology.
src/huey/memory/PY/__init__.py:23:_LEGACY_PREFIX = f"{__name__}.memory.PY"
src/huey/memory/PY/__init__.py:27:    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""
src/huey/memory/PY/__init__.py:30:        module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
src/huey/memory/PY/ai_processor.py:310:        This helper mirrors the legacy interface used by a number of examples
src/huey/memory/PY/api.py:38:# the legacy ``huey`` tree. When those modules are unavailable (for example in
src/huey/memory/PY/api.py:48:        """Minimal stand-in for the legacy :class:`AIProcessor`."""
src/huey/memory/PY/honeycomb_backup.py:1:"""Legacy import path forwarding to :mod:`huey.honeycomb.backup`."""
src/huey/memory/PY/honeycomb_index.py:1:"""Legacy import path forwarding to :mod:`huey.honeycomb.index`."""
src/huey/memory/PY/honeycomb_monitor.py:1:"""Legacy import path forwarding to :mod:`huey.honeycomb.monitor`."""
src/huey/memory/PY/honeycomb_retention.py:1:"""Legacy import path forwarding to :mod:`huey.honeycomb.retention`."""
src/huey/memory/PY/honeycomb_storage.py:1:"""Legacy import path forwarding to :mod:`huey.honeycomb.storage`."""
src/huey/memory/PY/main.py:6:"""Expose the legacy :mod:`monkey_head.main` implementation under ``huey``.
src/huey/memory/PY/pygpt_custom_cli.py:6:"""Lightweight CLI integration mimicking the legacy PyHuey launcher."""
src/huey/memory/PY/pygpt_integration.py:119:            name="legacy-root",
src/huey/memory/PY/pygpt_integration.py:122:            kind="legacy",
src/huey/memory/PY/pygpt_integration.py:126:            name="legacy-root-src",
src/huey/memory/PY/pygpt_integration.py:129:            kind="legacy",
src/huey/memory/PY/pygpt_integration.py:133:            name="legacy-repo",
src/huey/memory/PY/pygpt_integration.py:136:            kind="legacy",
src/huey/memory/PY/pygpt_memory.py:12:    """A minimal conversation buffer compatible with the legacy PyGPT tooling."""
src/huey/memory/PY/run.py:268:        except ImportError:  # pragma: no cover - fallback to legacy package
src/huey/memory/PY/run.py:277:        except ImportError:  # pragma: no cover - fallback to legacy package
src/huey/memory/PY/run.py:315:            from .legacy.simple_chat import main as simple_chat_main
src/huey/memory/PY/run.py:316:        except ImportError as exc:  # pragma: no cover - optional legacy feature
src/huey/memory/PY/update_sources_to_trixie.py:5:# MIGRATION-ONLY: historical helper retained for legacy Debian Trixie nodes.
src/huey/memory/PY/update_sources_to_trixie.py:17:This legacy script defaults to ``trixie`` for old nodes. Active installs should
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:73:* carrying legacy hardware, legacy thought, and legacy craftsmanship forward into a modern architecture,
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:76:But this ethos is not sentimental. Legacy hardware is not preserved merely because it is old. It is preserved when its native strength still justifies the energy required to integrate it.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:80:> A legacy system is worth keeping when what it does best can still be used with a favorable ratio of value, time, power, and complexity.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:169:   Old technologies, salvaged materials, legacy machines, and inherited ideas are not automatically obsolete. They may be repurposed, translated, or carried forward if they still serve the architecture honestly.
src/huey/memory/TXT/04 - HIMS.txt:529:- legacy shell interfaces,
src/huey/memory/__init__.py:6:"""Legacy memory package wrapper for HueyOS."""
src/huey/memory/__init__.py:21:_LEGACY_PREFIX = f"{__name__}.PY"
src/huey/memory/__init__.py:25:    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""
src/huey/memory/__init__.py:28:        module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
src/huey/memory/core/system_checks.py:1:"""Re-export ``huey.core.system_checks`` for legacy import paths."""
src/huey/memory/utils/commands.py:11:# Re-export public attributes for callers expecting the legacy module layout.
src/huey/pdf_chat.py:1:# Auto-generated bridge to legacy module
src/huey/pdf_pre_digestion.py:1:# Auto-generated bridge to legacy module
src/huey/power/management.py:365:            legacy = "pm-hibernate" if action == "hibernate" else "pm-suspend"
src/huey/power/management.py:366:            if shutil.which(legacy):
src/huey/power/management.py:367:                return [legacy]
src/huey/prompts/Monkey-Head-Project.json:146:      "dynamics": ["priority scheduling", "HAL + middleware legacy/modern bridge"],
src/huey/prompts/Monkey-Head-Project.json:241:      "transmitter": "Legacy bridge; high-level intents"
src/huey/prompts/Monkey-Head-Project.json:260:          "MacBook Pro 2012 ΓÇö transmitter/legacy bridge"
src/huey/prompts/Monkey-Head-Project.json:268:  "legacy_integration": {
src/huey/prompts/Monkey-Head-Project.json:273:    "source": "Legacy Hardware integration notes."
src/huey/prompts/Monkey-Head-Project.json:321:      "lesson": "adaptability over permanence; legacy requires humility and iteration",
src/huey/prompts/OLD/1) Monkey Head Project [Thesis].txt:24:- **Legacy Hardware Integration**: Incorporating platforms like the **Commodore VIC-20, C64, and C128** not only preserves historical computing insights but also illustrates how **older devices** can be revitalized through modern architectures, supporting both educational and practical objectives.
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:12:Inspired by themes of **grandeur**, **ambition**, and **legacy**, ΓÇ£OzymandiasΓÇ¥ symbolizes both the power of human achievement and the inevitability of decline. This duality informs the **Monkey Head Project**, underscoring that genuine innovation demands ambition moderated by humility.
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:55:Compatibility hurdlesΓÇöparticularly between **legacy** and **state-of-the-art** hardwareΓÇöhave largely been overcome, creating a **rich**, **interconnected** environment uniting historical contexts, computational strength, and modern data processing.
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:72:The poemΓÇÖs reminder of **impermanence** calls the Project to aim not only for near-term success but also a **sustained, far-reaching legacy**. As the Project advances, it must resist complacency, instead seeking **lasting impact** beyond ephemeral achievements.
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:83:In the spirit of *Ozymandias*, the Project remembers that **ambition** demands **continuous** effort, **adaptive** thinking, and **ethical** grounding. True success transcends technical triumphΓÇöit must also reflect **resilience**, **flexibility**, and principled innovation. By persistently evolving under these guiding values, the Monkey Head Project aspires to establish a legacy that withstands the erosion of time, forging an enduring contribution to **robotics** and **AI**.
src/huey/prompts/OLD/20) Final Chapter [The Future].txt:82:By merging **ambition** with **rigorous methodology**, **ethical oversight**, and a **communal ethos**, the Monkey Head Project aspires to more than technical success. It aims to pioneer a **culture** of exploration and shared growth, standing on the legacy of landmark technologiesΓÇöfrom *legacy Commodore hardware* to **Huey**ΓÇöto forge bold new paths in the collective scientific imagination.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:28:A curated suite of Apple devices supports **development**, **deployment**, and **legacy integration** within the Command Center:
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:32:- **MacBook Pro (2012)**: Designated the ΓÇ£Transmitter,ΓÇ¥ ensuring backward compatibility with legacy systems and acting as a **bridge** between modern innovations and older peripherals.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:9:Within the Monkey Head Project, the **MacBook Pro 2012** (non-Retina) serves as the **ΓÇ£Transmitter,ΓÇ¥** specializing in interactions with legacy hardware and software. Despite its age, this MacBookΓÇÖs adaptability and rich connectivity options make it vital for bridging older systems and the ProjectΓÇÖs cutting-edge developments, ensuring **broad compatibility** and **inclusivity**.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:17:   - Though not state-of-the-art, it meets the ProjectΓÇÖs needs for reliable operation of legacy applications and essential tasks.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:25:   - **Intel HD Graphics 4000**, sufficient for basic graphical tasks and interfacing with legacy software requiring minimal GPU resources.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:35:#### 1. Legacy System Compatibility Testing
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:38:- **Legacy Software Suites**: Runs performance checks to confirm new Project features operate smoothly on older systems (VIC-20, C64, C128, etc.).  
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:44:- **Peripheral Integration**: Links legacy audio interfaces, external drives, and diagnostic equipment to newer systems, facilitating data transfer and persistent operational capabilities.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:71:By maintaining this connection between emerging tech and legacy hardware, the **MacBook Pro 2012** ensures the Monkey Head ProjectΓÇÖs innovations reach a larger, more diverse user base.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:76:**Backward compatibility** with older devices enables widespread adoption of the ProjectΓÇÖs AI and robotics solutions, spanning high-end laboratories and legacy-focused facilities alike.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:83:Acting as the **Transmitter**, the **MacBook Pro 2012** is indispensable to the Monkey Head Project, ensuring new advancements remain compatible with **past technologies**. Its specialized role in **legacy compatibility testing**, **communication bridging**, and **dual-boot** operation exemplifies the ProjectΓÇÖs commitment to **inclusivity** and **broader technological reach**. By unifying past and present, the MacBook Pro 2012 upholds the ProjectΓÇÖs foundational ethosΓÇömaking **cutting-edge** robotics and AI accessible to **all**.
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:35:   - **Middleware Interfaces**: Bridges new and legacy systems, ensuring older components remain interoperable with modern frameworks without compromising stability or flexibility.
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:2:Below is a **refined, cohesive** version of your text on integrating the **VIC-20**, **Commodore 64**, and **Commodore 128** within the **Monkey Head Project**ΓÇÖs Huey AI/OS. It retains the original structure and details, clarifying the importance, technical steps, and future directions of this legacy integration.
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:6:## VIC-20, C64, C128: Integrated Legacy Hardware
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:16:   - **Preservation & Education**: The VIC-20, C64, and C128 remain influential milestones in computing history. HueyΓÇÖs seamless operation on these devices honors their legacy, offering hands-on educational experiences that illustrate how programming languages and architectures have evolved.  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:19:2. **Legacy Compatibility**  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:29:   - **VICE Emulator**: Offers full system emulation, bridging legacy architectures with HueyΓÇÖs AI environment for real-time data exchange alongside contemporary components.
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:48:   - **Prototyping & Testing**: Legacy architecture forces developers to refine code structure, verifying that solutions remain lean and efficient.  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:64:   - **Collaborative Creativity**: Community events focus on creating or repurposing applications for these legacy systems, now augmented by HueyΓÇÖs modern features.  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:71:1. **Expansion of Legacy Support**  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:81:The integration of **VIC-20**, **Commodore 64**, and **C128** into the Monkey Head Project is far more than nostalgic preservation; it exemplifies how **classic systems** remain valuable within a **cutting-edge AI/OS** framework like **Huey**. By revitalizing legacy machines through **modern connectivity**, **expanded memory**, and **innovative software enhancements**, the Project breathes new life into historical computing platformsΓÇödemonstrating the trajectory from early microprocessors to sophisticated, adaptive AI. This initiative not only preserves computing heritage but enriches the modern landscape with insights, educational value, and ever-evolving community engagement.
src/huey/prompts/master-plan-v2-final.json:89:    "legacy_context": "Historical 6.18.2 references remain only for compatibility archives and fixtures; active guidance follows role-based 7.0 kernel naming.",
src/huey/prompts/master-plan-v3.json:101:      "legacy_context": "6.18.2-series names are retained only in compatibility fixtures and historical archives.",
src/huey/prompts/master-plan-v5.json:117:      "legacy_context": "6.18.2-series names are retained only in compatibility fixtures and historical archives.",
src/huey/pygpt_custom_cli.py:8:This wrapper keeps legacy imports stable while routing to the richer
src/huey/pygpt_memory.py:1:# Auto-generated bridge to legacy module
src/huey/pygpt_net/controller/agent/__init__.py:19:from .legacy import Legacy
src/huey/pygpt_net/controller/agent/__init__.py:34:        self.legacy = Legacy(window)
src/huey/pygpt_net/controller/agent/__init__.py:38:        self.legacy.setup()
src/huey/pygpt_net/controller/agent/__init__.py:43:        self.legacy.reload()
src/huey/pygpt_net/controller/agent/__init__.py:48:        self.legacy.on_stop()
src/huey/pygpt_net/controller/agent/common.py:31:        """Enable auto stop (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:36:        """Disable auto stop (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:42:        Toggle auto stop (Legacy)
src/huey/pygpt_net/controller/agent/common.py:52:        """Enable always continue (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:57:        """Disable always continue (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:63:        Toggle always continue (Legacy)
src/huey/pygpt_net/controller/agent/common.py:79:        # legacy
src/huey/pygpt_net/controller/agent/common.py:98:        """Show agent status (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:102:        """Hide agent status (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:106:        """Toggle agent status (Legacy)"""
src/huey/pygpt_net/controller/agent/common.py:108:        if mode in [MODE_AGENT] or self.window.controller.agent.legacy.is_inline():
src/huey/pygpt_net/controller/agent/experts.py:77:        if self.window.controller.agent.legacy.enabled():
src/huey/pygpt_net/controller/agent/experts.py:88:                self.window.controller.agent.legacy.enabled()
src/huey/pygpt_net/controller/agent/experts.py:99:            sys_prompt = self.window.controller.agent.legacy.on_system_prompt(
src/huey/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/controller/agent)
src/huey/pygpt_net/controller/agent/legacy.py:27:class Legacy:
src/huey/pygpt_net/controller/agent/legacy.py:35:        self.iteration = 0  # legacy
src/huey/pygpt_net/controller/agent/legacy.py:194:        self.window.controller.agent.legacy.update()  # update status
src/huey/pygpt_net/controller/agent/legacy.py:228:            self.window.controller.agent.legacy.update()  # update status
src/huey/pygpt_net/core/agents/__init__.py:17:from .legacy import Legacy
src/huey/pygpt_net/core/agents/__init__.py:33:        self.legacy = Legacy(window)
src/huey/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (huey/pygpt_net/core/agents)
src/huey/pygpt_net/core/agents/legacy.py:30:class Legacy:
src/huey/pygpt_net/core/agents/legacy.py:33:        Agents core (legacy)
src/huey/pygpt_net/data/config/modes.json:70:            "name": "Agent (legacy)",
src/huey/pygpt_net/data/config/settings.json:251:            {"legacy": "Legacy (markdown)"}
src/huey/pygpt_net/plugin/agent/__init__.py:107:                self.window.controller.agent.legacy.update()  # update agent status bar
src/huey/pygpt_net/plugin/agent/__init__.py:110:            self.window.controller.agent.legacy.update()  # update agent status bar
src/huey/pygpt_net/plugin/agent/__init__.py:144:        return pre_prompt + self.window.controller.agent.legacy.on_system_prompt(
src/huey/pygpt_net/plugin/agent/__init__.py:157:        return self.window.controller.agent.legacy.on_input_before(prompt)
src/huey/pygpt_net/plugin/agent/__init__.py:166:        self.window.controller.agent.legacy.cmd(ctx, cmds)  # force execute
src/huey/pygpt_net/plugin/agent/__init__.py:172:        self.window.controller.agent.legacy.on_stop()  # force stop
src/huey/pygpt_net/plugin/agent/__init__.py:180:        self.window.controller.agent.legacy.on_user_send(text)
src/huey/pygpt_net/plugin/agent/__init__.py:188:        self.window.controller.agent.legacy.on_ctx_end(
src/huey/pygpt_net/plugin/agent/__init__.py:199:        self.window.controller.agent.legacy.on_ctx_before(
src/huey/pygpt_net/plugin/agent/__init__.py:210:        self.window.controller.agent.legacy.on_ctx_after(ctx)
src/huey/pygpt_net/ui/layout/toolbox/agent.py:39:        option = self.window.controller.agent.legacy.options["agent.iterations"]
src/huey/run.py:6:"""Expose legacy runtime entry points under :mod:`huey.run`."""
src/huey/run.py:12:# NOTE(v101.1-migration): Compatibility wrapper for the legacy ``huey.run``
src/huey/run.py:34:    """Delegate unknown attributes to the legacy runtime module."""
src/huey/system_checks.py:329:    """Compatibility wrapper for legacy callers expecting this function name."""
src/huey/tensorflow_feed.py:1:# Auto-generated bridge to legacy module
src/huey/utils/__init__.py:8:from ..memory.PY import utils as _legacy_utils
src/huey/utils/__init__.py:12:calculate_sum = _legacy_utils.calculate_sum
src/huey/utils/__init__.py:13:convert_image = _legacy_utils.convert_image
src/huey/utils/__init__.py:14:convert_images_in_directory = _legacy_utils.convert_images_in_directory
src/huey/utils/__init__.py:15:convert_jpeg_to_png = _legacy_utils.convert_jpeg_to_png
src/huey/utils/__init__.py:16:setup_logging = _legacy_utils.setup_logging
src/huey/utils/__init__.py:17:validate_input = _legacy_utils.validate_input
src/hueyos/__init__.py:5:roots so regular imports such as ``hueyos.core.task_scheduler`` and legacy
src/hueyos/__init__.py:19:_LEGACY_DIR = _HUEY_DIR / "memory" / "PY"
src/hueyos/__init__.py:22:    str(path) for path in (_PACKAGE_DIR, _HUEY_DIR, _LEGACY_DIR) if path.is_dir()
src/hueyos/api/__init__.py:4:``hueyos.api.routers.system`` does not eagerly import the full legacy API app.
src/hueyos/api/app.py:1:"""Maintained ``hueyos.api`` app entrypoint with legacy compatibility.
src/hueyos/api/app.py:4:legacy implementation surface while the API is being split into smaller modules.
src/hueyos/api/app.py:9:from huey.memory.PY import api as _legacy_api
src/hueyos/api/app.py:11:app = _legacy_api.app
src/hueyos/api/app.py:12:main = _legacy_api.main
src/hueyos/api/app.py:13:SCHEDULER = _legacy_api.SCHEDULER
src/hueyos/api/app.py:19:    """Delegate unresolved attributes to the legacy API module."""
src/hueyos/api/app.py:21:    return getattr(_legacy_api, name)
src/hueyos/api/auth.py:3:For v101.1 stabilization these functions are re-exported from the legacy API
src/hueyos/api/auth.py:9:from huey.memory.PY import api as _legacy_api
src/hueyos/api/auth.py:11:_configured_api_token = _legacy_api._configured_api_token
src/hueyos/api/auth.py:12:_is_local_request = _legacy_api._is_local_request
src/hueyos/api/auth.py:13:_require_privileged_surface_access = _legacy_api._require_privileged_surface_access
src/hueyos/api/auth.py:15:    _legacy_api._require_unsafe_task_submission_access
src/hueyos/api/auth.py:17:_unsafe_task_submission_enabled = _legacy_api._unsafe_task_submission_enabled
src/hueyos/api/routers/network.py:1:"""Network API routes extracted from the legacy API module."""
src/hueyos/api/routers/network.py:12:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/network.py:14:    return legacy_api.network_status()
src/hueyos/api/routers/network.py:19:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/network.py:21:    legacy_api.require_strong_api_auth(request)
src/hueyos/api/routers/network.py:22:    return legacy_api.ensure_network_connectivity()
src/hueyos/api/routers/power.py:1:"""Power API routes extracted from the legacy API module."""
src/hueyos/api/routers/power.py:12:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/power.py:14:    return legacy_api.battery_status()
src/hueyos/api/routers/power.py:19:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/power.py:21:    return legacy_api.power_should_shutdown()
src/hueyos/api/routers/power.py:26:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/power.py:28:    legacy_api.require_strong_api_auth(request)
src/hueyos/api/routers/power.py:29:    return legacy_api.trigger_shutdown()
src/hueyos/api/routers/sensors.py:1:"""Sensor API routes extracted from the legacy API module."""
src/hueyos/api/routers/sensors.py:12:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:14:    return legacy_api.sensor_plugins()
src/hueyos/api/routers/sensors.py:19:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:21:    return legacy_api.list_sensors()
src/hueyos/api/routers/sensors.py:26:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:28:    return legacy_api.register_sensor(request)
src/hueyos/api/routers/sensors.py:33:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:35:    return legacy_api.remove_sensor(sensor_name)
src/hueyos/api/routers/sensors.py:40:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:42:    return legacy_api.poll_sensor(sensor_name)
src/hueyos/api/routers/sensors.py:47:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:49:    return legacy_api.poll_all_sensors()
src/hueyos/api/routers/sensors.py:59:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:61:    return legacy_api.sensor_history(sensor_name, limit=limit)
src/hueyos/api/routers/sensors.py:66:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:68:    return await legacy_api.stream_sensor(sensor_name)
src/hueyos/api/routers/sensors.py:73:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/sensors.py:75:    return await legacy_api.stream_all_sensors()
src/hueyos/api/routers/system.py:1:"""System and health API routes extracted from the legacy API module."""
src/hueyos/api/routers/tasks.py:15:def _legacy_api_module():
src/hueyos/api/routers/tasks.py:16:    from huey.memory.PY import api as legacy_api
src/hueyos/api/routers/tasks.py:18:    return legacy_api
src/hueyos/api/routers/tasks.py:27:    legacy_api = _legacy_api_module()
src/hueyos/api/routers/tasks.py:28:    legacy_api.require_strong_api_auth(http_request)
src/hueyos/api/routers/tasks.py:29:    legacy_api._require_unsafe_task_submission_access(http_request)
src/hueyos/api/routers/tasks.py:35:    record = legacy_api.SCHEDULER.submit_task(
src/hueyos/api/routers/tasks.py:56:    legacy_api = _legacy_api_module()
src/hueyos/api/routers/tasks.py:57:    legacy_api.require_strong_api_auth(http_request)
src/hueyos/api/routers/tasks.py:58:    records = legacy_api.SCHEDULER.list_tasks(status_filter)
src/hueyos/api/routers/tasks.py:68:    legacy_api = _legacy_api_module()
src/hueyos/api/routers/tasks.py:69:    legacy_api.require_strong_api_auth(http_request)
src/hueyos/api/routers/tasks.py:71:        record = legacy_api.SCHEDULER.get_task(task_id)
src/hueyos/api/routers/tasks.py:87:    legacy_api = _legacy_api_module()
src/hueyos/api/routers/tasks.py:88:    legacy_api.require_strong_api_auth(http_request)
src/hueyos/api/routers/tasks.py:90:        record = legacy_api.SCHEDULER.cancel_task(task_id)
src/hueyos/cli/commands/memory.py:9:def _legacy_handler(name: str) -> Callable[[argparse.Namespace], int]:
src/hueyos/cli/commands/memory.py:11:        from huey.memory.PY import cli as legacy_cli
src/hueyos/cli/commands/memory.py:13:        return getattr(legacy_cli, name)(args)
src/hueyos/cli/commands/memory.py:21:    """Register memory-oriented command groups via legacy handlers."""
src/hueyos/cli/commands/memory.py:44:    sort_cmd.set_defaults(handler=_legacy_handler("_cmd_memory_sort"))
src/hueyos/cli/commands/runtime.py:9:def _legacy_handler(name: str) -> Callable[[argparse.Namespace], int]:
src/hueyos/cli/commands/runtime.py:11:        from huey.memory.PY import cli as legacy_cli
src/hueyos/cli/commands/runtime.py:13:        return getattr(legacy_cli, name)(args)
src/hueyos/cli/commands/runtime.py:21:    """Register runtime and utility commands via legacy handlers."""
src/hueyos/cli/commands/runtime.py:37:    init_cmd.set_defaults(handler=_legacy_handler("_cmd_init"))
src/hueyos/cli/commands/runtime.py:86:    run_cmd.set_defaults(handler=_legacy_handler("_cmd_run"))
src/hueyos/cli/commands/runtime.py:115:    deploy_cmd.set_defaults(handler=_legacy_handler("_cmd_deploy"))
src/hueyos/cli/commands/runtime.py:129:    agent_cmd.set_defaults(handler=_legacy_handler("_cmd_agent_status"))
src/hueyos/cli/commands/runtime.py:148:    v1_run_cmd.set_defaults(handler=_legacy_handler("_cmd_v1_run"))
src/hueyos/cli/commands/runtime.py:169:    v1_run_queue_cmd.set_defaults(handler=_legacy_handler("_cmd_v1_run_queue"))
src/hueyos/core/resilience.py:1:"""Compatibility shim exposing legacy huey.core.resilience via hueyos.core.resilience."""
src/hueyos/core/task_scheduler.py:1:"""Compatibility shim exposing legacy huey.core.task_scheduler via hueyos.core.task_scheduler."""
src/hueyos/hardware/__init__.py:1:"""Compatibility shim exposing legacy huey.hardware via hueyos.hardware."""
src/hueyos/hardware/plugins.py:1:"""Compatibility shim exposing legacy huey.hardware.plugins via hueyos.hardware.plugins."""
src/hueyos/honeycomb/__init__.py:4:legacy ``huey.honeycomb`` modules remain compatibility shims.
src/hueyos/network.py:1:"""Compatibility shim exposing legacy huey.network via hueyos.network."""
src/hueyos/pdf_utils.py:1:"""Compatibility shim exposing legacy huey.pdf_utils via hueyos.pdf_utils."""
src/hueyos/power.py:1:"""Compatibility shim exposing legacy huey.power via hueyos.power."""
src/hueyos/scripts/__init__.py:12:_LEGACY_DIR = _SRC_DIR / "huey" / "memory" / "PY"
src/hueyos/scripts/__init__.py:16:    for path in (_PACKAGE_DIR, _HUEY_SCRIPTS_DIR, _LEGACY_DIR)
src/hueyos/services/__init__.py:12:_LEGACY_DIR = _SRC_DIR / "huey" / "memory" / "PY"
src/hueyos/services/__init__.py:16:    for path in (_PACKAGE_DIR, _HUEY_SERVICES_DIR, _LEGACY_DIR)
src/hueyos/system_checks.py:1:"""Compatibility shim exposing legacy huey.system_checks via hueyos.system_checks."""
src/hueyos/utils/__init__.py:3:Modern helpers live under :mod:`huey.utils`; several legacy helpers still live
src/hueyos/utils/__init__.py:17:_LEGACY_DIR = _SRC_DIR / "huey" / "memory" / "PY"
src/hueyos/utils/__init__.py:20:    str(path) for path in (_PACKAGE_DIR, _HUEY_UTILS_DIR, _LEGACY_DIR) if path.is_dir()
src/hueyos/utils/auto_sort.py:1:"""Compatibility shim exposing legacy huey.utils.auto_sort via hueyos.utils.auto_sort."""
src/hueyos/utils/paths.py:1:"""Compatibility shim exposing legacy huey.utils.paths via hueyos.utils.paths."""
tests/test_cli.py:15:from huey.memory.PY import cli as legacy_cli
tests/test_cli.py:37:def test_direct_legacy_cli_module_invocation_system_check(monkeypatch, capsys):
tests/test_cli.py:45:    exit_code = legacy_cli.main(["system-check", "--json"])
tests/test_huey_compat_imports.py:1:"""Compatibility smoke tests for legacy ``huey`` import paths."""
tests/test_huey_compat_imports.py:55:def test_import_api_through_legacy_and_new_paths():
tests/test_huey_compat_imports.py:56:    legacy = importlib.import_module("huey.api")
tests/test_huey_compat_imports.py:59:    assert legacy.app is maintained.app
tests/test_huey_compat_imports.py:60:    assert callable(legacy.main)
tests/test_hueyos_namespace.py:11:def test_hueyos_package_path_exposes_current_and_legacy_roots():
tests/test_hueyos_namespace.py:19:def test_hueyos_imports_modern_and_legacy_submodules():
tests/test_hueyos_namespace.py:36:def test_hueyos_local_modules_override_legacy_bridges():
tests/test_legacy_connectors.py:4:# HueyOS: Test Legacy Connectors module (tests)
tests/test_legacy_connectors.py:10:from hueyos.legacy.connectors import (
tests/test_legacy_connectors.py:11:    EmulatedLegacyConnector,
tests/test_legacy_connectors.py:12:    LegacyConnectorFactory,
tests/test_legacy_connectors.py:13:    SerialLegacyConnector,
tests/test_legacy_connectors.py:19:    connector = EmulatedLegacyConnector()
tests/test_legacy_connectors.py:36:    monkeypatch.setattr("hueyos.legacy.connectors.serial", None)
tests/test_legacy_connectors.py:37:    connector = SerialLegacyConnector(port="/dev/ttyUSB0")
tests/test_legacy_connectors.py:42:def test_legacy_connector_factory_defaults_to_emulated():
tests/test_legacy_connectors.py:43:    connector = LegacyConnectorFactory.create({})
tests/test_legacy_connectors.py:44:    assert isinstance(connector, EmulatedLegacyConnector)
tests/test_legacy_connectors.py:48:    instance = LegacyConnectorFactory.create(config)
tests/test_legacy_connectors.py:49:    assert isinstance(instance, SerialLegacyConnector)
tests/test_run_entrypoint.py:1:"""Tests for the legacy ``huey.run`` entry point wrapper."""
tests/test_system_checks_module.py:18:def test_check_os_support_warns_for_legacy_windows(monkeypatch, caplog):
vendor/pygpt/README.md:12:4. legacy checkout locations.
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:19:from .legacy import Legacy
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:34:        self.legacy = Legacy(window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:38:        self.legacy.setup()
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:43:        self.legacy.reload()
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/__init__.py:48:        self.legacy.on_stop()
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:31:        """Enable auto stop (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:36:        """Disable auto stop (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:42:        Toggle auto stop (Legacy)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:52:        """Enable always continue (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:57:        """Disable always continue (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:63:        Toggle always continue (Legacy)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:79:        # legacy
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:98:        """Show agent status (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:102:        """Hide agent status (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:106:        """Toggle agent status (Legacy)"""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/common.py:108:        if mode in [MODE_AGENT] or self.window.controller.agent.legacy.is_inline():
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:77:        if self.window.controller.agent.legacy.enabled():
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:88:                self.window.controller.agent.legacy.enabled()
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/experts.py:99:            sys_prompt = self.window.controller.agent.legacy.on_system_prompt(
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/controller/agent)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:27:class Legacy:
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:35:        self.iteration = 0  # legacy
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:194:        self.window.controller.agent.legacy.update()  # update status
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/agent/legacy.py:228:            self.window.controller.agent.legacy.update()  # update status
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:17:from .legacy import Legacy
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/__init__.py:33:        self.legacy = Legacy(window)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:6:# HueyOS: Legacy module (repo/pygpt-MHP/src/pygpt_net/core/agents)
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:30:class Legacy:
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/legacy.py:33:        Agents core (legacy)
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/modes.json:70:            "name": "Agent (legacy)",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:251:            {"legacy": "Legacy (markdown)"}
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:107:                self.window.controller.agent.legacy.update()  # update agent status bar
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:110:            self.window.controller.agent.legacy.update()  # update agent status bar
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:144:        return pre_prompt + self.window.controller.agent.legacy.on_system_prompt(
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:157:        return self.window.controller.agent.legacy.on_input_before(prompt)
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:166:        self.window.controller.agent.legacy.cmd(ctx, cmds)  # force execute
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:172:        self.window.controller.agent.legacy.on_stop()  # force stop
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:180:        self.window.controller.agent.legacy.on_user_send(text)
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:188:        self.window.controller.agent.legacy.on_ctx_end(
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:199:        self.window.controller.agent.legacy.on_ctx_before(
vendor/pygpt/pygpt-mhp/src/pygpt_net/plugin/agent/__init__.py:210:        self.window.controller.agent.legacy.on_ctx_after(ctx)
vendor/pygpt/pygpt-mhp/src/pygpt_net/ui/layout/toolbox/agent.py:39:        option = self.window.controller.agent.legacy.options["agent.iterations"]

## deprecated

audit-requirements.txt:205:deprecated==1.3.1
docs/unsorted/repository-restructure-inventory.md:28:- `gui/` ΓåÆ `apps/huey_gui/` (if still active) or `archives/gui-prototypes/` (if deprecated)
docs/unsorted/repository-restructure-recommendation.md:46:   - Keep active Python runtime in one place and mark duplicates as deprecated with README pointers.
master-plan-v101.1.json:461:        "status": "deprecated as the active name for the physical proof body in V31.0",
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:1728:Description: ISC DHCP Client for debian-installer (deprecated)
platform/windows/huey/pyhuey/requirements-known-good-freeze.txt:43:Deprecated==1.2.18
platform/windows/huey/pyhuey/requirements-known-good-with-redis-freeze.txt:43:Deprecated==1.2.18
requirements.txt:206:deprecated==1.3.1
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:189:The method does not erase its older selves blindly. Earlier versions, failed routes, deprecated structures, and abandoned hardware ideas remain useful as archive, contrast, and explanation. But they should not be mistaken for the current baseline.

## old

.github/ISSUE_TEMPLATE/bug_report.yml:30:      placeholder: "Python 3.11.9"
.github/ISSUE_TEMPLATE/bug_report.yml:50:      placeholder: "python -m huey --help"
.github/ISSUE_TEMPLATE/docs_issue.yml:18:      placeholder: "README.md section 'Installation'"
.github/workflows/security-artifact-container-scan.yml:33:          THRESHOLDS = [
.github/workflows/security-artifact-container-scan.yml:70:          for limit, label in THRESHOLDS:
.github/workflows/security-artifact-container-scan.yml:81:                  lines.append("No tracked files at this threshold.")
.migration/inventory/git-ls-files.pass-01.txt:94:integrations/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:714:platform/packaging/pool-udeb/main/o/oldsys-preseed/oldsys-preseed_3.24_amd64.udeb
.migration/inventory/git-ls-files.pass-01.txt:996:src/huey/memory/MD/placeholder-occurrences.md
.migration/inventory/git-ls-files.pass-01.txt:1280:src/huey/prompts/OLD/1) Monkey Head Project [Thesis].txt
.migration/inventory/git-ls-files.pass-01.txt:1281:src/huey/prompts/OLD/10) Hierarchical Structures [HostOS-SubOS-NanoOS].txt
.migration/inventory/git-ls-files.pass-01.txt:1282:src/huey/prompts/OLD/11) Carpenter Ants & Fungi [Hierarchical Structure].txt
.migration/inventory/git-ls-files.pass-01.txt:1283:src/huey/prompts/OLD/12) Borg Queen & SG1 Replicators [Adaptability].txt
.migration/inventory/git-ls-files.pass-01.txt:1284:src/huey/prompts/OLD/13) Conductor & Symphony [Nodes].txt
.migration/inventory/git-ls-files.pass-01.txt:1285:src/huey/prompts/OLD/14) McCoy Hypothetical [Augmented Transporter Theory].txt
.migration/inventory/git-ls-files.pass-01.txt:1286:src/huey/prompts/OLD/15) Bees & Honey [Custom 'Honeycomb' Storage].txt
.migration/inventory/git-ls-files.pass-01.txt:1287:src/huey/prompts/OLD/16) Bifurcation [Exact & Augmented].txt
.migration/inventory/git-ls-files.pass-01.txt:1288:src/huey/prompts/OLD/17) Parasitic Protocol [Crashed Shuttle Scenario].txt
.migration/inventory/git-ls-files.pass-01.txt:1289:src/huey/prompts/OLD/18) Plane & Submarine Logistics [Safety].txt
.migration/inventory/git-ls-files.pass-01.txt:1290:src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt
.migration/inventory/git-ls-files.pass-01.txt:1291:src/huey/prompts/OLD/2) Huey [Dual Motherboards].txt
.migration/inventory/git-ls-files.pass-01.txt:1292:src/huey/prompts/OLD/20) Final Chapter [The Future].txt
.migration/inventory/git-ls-files.pass-01.txt:1293:src/huey/prompts/OLD/3) The Lab  [Command Center].txt
.migration/inventory/git-ls-files.pass-01.txt:1294:src/huey/prompts/OLD/4) MacBook Pro 2019 [Daily Driver].txt
.migration/inventory/git-ls-files.pass-01.txt:1295:src/huey/prompts/OLD/5) iMac 5K 2017 [Universal Display].txt
.migration/inventory/git-ls-files.pass-01.txt:1296:src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt
.migration/inventory/git-ls-files.pass-01.txt:1297:src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt
.migration/inventory/git-ls-files.pass-01.txt:1298:src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt
.migration/inventory/git-ls-files.pass-01.txt:1299:src/huey/prompts/OLD/9) Cloud Pyramid [Federation Constitution].txt
.migration/inventory/git-ls-files.pass-01.txt:1300:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_1.pdf
.migration/inventory/git-ls-files.pass-01.txt:1301:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_2.pdf
.migration/inventory/git-ls-files.pass-01.txt:1302:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_3.pdf
.migration/inventory/git-ls-files.pass-01.txt:1303:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_4.pdf
.migration/inventory/git-ls-files.pass-01.txt:1304:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_5.pdf
.migration/inventory/git-ls-files.pass-01.txt:1305:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_6.pdf
.migration/inventory/git-ls-files.pass-01.txt:1306:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_7.pdf
.migration/inventory/git-ls-files.pass-01.txt:1307:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_8.pdf
.migration/inventory/git-ls-files.pass-01.txt:1308:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_9.pdf
.migration/inventory/git-ls-files.pass-01.txt:1309:src/huey/prompts/OLD/Monkey_Head_Project_Chapter_X.pdf
.migration/inventory/git-ls-files.pass-01.txt:1310:src/huey/prompts/OLD/Monkey_Head_Project_Preamble.pdf
.migration/inventory/git-ls-files.pass-01.txt:1357:src/huey/pygpt_net/controller/config/placeholder.py
.migration/inventory/git-ls-files.pass-01.txt:1480:tests/test_placeholder.py
.security/bandit-baseline.json:2397:    "src/huey/pygpt_net/controller/config/placeholder.py": {
LICENSE:100:A ΓÇ£User ProductΓÇ¥ is either (1) a ΓÇ£consumer productΓÇ¥, which means any tangible personal property which is normally used for personal, family, or household purposes, or (2) anything designed or sold for incorporation into a dwelling. In determining whether a product is a consumer product, doubtful cases shall be resolved in favor of coverage. For a particular product received by a particular user, ΓÇ£normally usedΓÇ¥ refers to a typical or common use of that class of product, regardless of the status of the particular user or of the way in which the particular user actually uses, or expects or is expected to use, the product. A product is a consumer product regardless of whether the product has substantial commercial, industrial or non-consumer uses, unless such uses represent the only significant mode of use of the product.
LICENSE:116:Notwithstanding any other provision of this License, for material you add to a covered work, you may (if authorized by the copyright holders of that material) supplement the terms of this License with terms:
LICENSE:134:However, if you cease all violation of this License, then your license from a particular copyright holder is reinstated (a) provisionally, unless and until the copyright holder explicitly and finally terminates your license, and (b) permanently, if the copyright holder fails to notify you of the violation by some reasonable means prior to 60 days after the cessation.
LICENSE:136:Moreover, your license from a particular copyright holder is reinstated permanently if the copyright holder notifies you of the violation by some reasonable means, this is the first time you have received notice of violation of this License (for any work) from that copyright holder, and you cure the violation prior to 30 days after your receipt of the notice.
LICENSE:154:A ΓÇ£contributorΓÇ¥ is a copyright holder who authorizes use under this License of the Program or a work on which the Program is based. The work thus licensed is called the contributorΓÇÖs ΓÇ£contributor versionΓÇ¥.
LICENSE:186:Later license versions may give you additional or different permissions. However, no additional obligations are imposed on any author or copyright holder as a result of your choosing to follow a later version.
LICENSE:190:THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM ΓÇ£AS ISΓÇ¥ WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
LICENSE:194:IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
README.md:209:| **~80 GB VRAM threshold** | Later local identity proof target |
README.md:506:queue / watched folder ΓåÆ sequential fixture processing ΓåÆ structured logs
README.md:572:### Future identity threshold
README.md:574:The later identity threshold remains:
README.md:1175:- manual bring-up followed by deterministic queue/watch-folder processing.
README.md:1217:- exact queue/watch-folder implementation,
SECURITY.md:33:Older versions are **unsupported** unless explicitly noted in a security advisory (for example, if an older line is widely deployed and warrants a one-off fix).
SECURITY.md:213:   * Evaluated for backporting to older lines if widely deployed and risk is high
SECURITY.md:269:* Attacks requiring **unreasonable physical access** for an on-robot context (e.g., direct bus probing, cold-boot lab attacks)
apps/huey_gui/main_ui.py:1:"""Minimal GUI scaffolding for tests."""
docs/_build/html/_sources/development/v101.1-namespace-migration.md.txt:8:- No runtime behavior has changed in this scaffold task.
docs/_build/html/_sources/development/v101.1-namespace-migration.md.txt:12:- Adds empty maintained namespace scaffolding under `src/hueyos/` for `api`, `cli`, `core`, and `runtime`.
docs/_build/html/_sources/security/security-hardening-status.md.txt:52:3. Maintain a checked-in template (for example, `.env.example`) containing placeholders only.
docs/_build/html/_static/basic.css:119:    font-weight: bold;
docs/_build/html/_static/basic.css:129:    font-weight: bold;
docs/_build/html/_static/basic.css:260:    font-weight: bold;
docs/_build/html/_static/basic.css:318:    font-weight: bold;
docs/_build/html/_static/basic.css:339:    font-weight: bold;
docs/_build/html/_static/basic.css:352:    font-weight: bold;
docs/_build/html/_static/basic.css:357:    font-weight: bold;
docs/_build/html/_static/basic.css:506:    font-weight: bold;
docs/_build/html/_static/basic.css:635:    font-weight: bold;
docs/_build/html/_static/basic.css:690:    font-weight: bold;
docs/_build/html/_static/basic.css:846:    font-weight: bold;
docs/_build/html/_static/pygments.css:11:.highlight .k { color: #004461; font-weight: bold } /* Keyword */
docs/_build/html/_static/pygments.css:16:.highlight .p { color: #000; font-weight: bold } /* Punctuation */
docs/_build/html/_static/pygments.css:27:.highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
docs/_build/html/_static/pygments.css:31:.highlight .gs { color: #000; font-weight: bold } /* Generic.Strong */
docs/_build/html/_static/pygments.css:32:.highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
docs/_build/html/_static/pygments.css:33:.highlight .gt { color: #A40000; font-weight: bold } /* Generic.Traceback */
docs/_build/html/_static/pygments.css:34:.highlight .kc { color: #004461; font-weight: bold } /* Keyword.Constant */
docs/_build/html/_static/pygments.css:35:.highlight .kd { color: #004461; font-weight: bold } /* Keyword.Declaration */
docs/_build/html/_static/pygments.css:36:.highlight .kn { color: #004461; font-weight: bold } /* Keyword.Namespace */
docs/_build/html/_static/pygments.css:37:.highlight .kp { color: #004461; font-weight: bold } /* Keyword.Pseudo */
docs/_build/html/_static/pygments.css:38:.highlight .kr { color: #004461; font-weight: bold } /* Keyword.Reserved */
docs/_build/html/_static/pygments.css:39:.highlight .kt { color: #004461; font-weight: bold } /* Keyword.Type */
docs/_build/html/_static/pygments.css:49:.highlight .ne { color: #C00; font-weight: bold } /* Name.Exception */
docs/_build/html/_static/pygments.css:55:.highlight .nt { color: #004461; font-weight: bold } /* Name.Tag */
docs/_build/html/_static/pygments.css:57:.highlight .ow { color: #004461; font-weight: bold } /* Operator.Word */
docs/_build/html/_static/pygments.css:58:.highlight .pm { color: #000; font-weight: bold } /* Punctuation.Marker */
docs/_build/html/audits/v101.1-repo-control-paths.html:81:      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Search"/>
docs/_build/html/development/v101.1-namespace-migration.html:43:<li><p>No runtime behavior has changed in this scaffold task.</p></li>
docs/_build/html/development/v101.1-namespace-migration.html:47:<li><p>Adds empty maintained namespace scaffolding under <code class="docutils literal notranslate"><span class="pre">src/hueyos/</span></code> for <code class="docutils literal notranslate"><span class="pre">api</span></code>, <code class="docutils literal notranslate"><span class="pre">cli</span></code>, <code class="docutils literal notranslate"><span class="pre">core</span></code>, and <code class="docutils literal notranslate"><span class="pre">runtime</span></code>.</p></li>
docs/_build/html/development/v101.1-namespace-migration.html:73:      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Search"/>
docs/_build/html/genindex.html:60:      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Search"/>
docs/_build/html/index.html:85:      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Search"/>
docs/_build/html/searchindex.js:1:Search.setIndex({"alltitles":{"1) pip-audit (Python dependency vulnerabilities)":[[3,"pip-audit-python-dependency-vulnerabilities"]],"2) Bandit (Python static security linting)":[[3,"bandit-python-static-security-linting"]],"3) Secret scanning":[[3,"secret-scanning"]],"Compatibility-path decision":[[0,"compatibility-path-decision"]],"Core Docs":[[2,null]],"Docker image pinning policy":[[3,"docker-image-pinning-policy"]],"Environment-specific guidance":[[3,"environment-specific-guidance"]],"Local security checks":[[3,"local-security-checks"]],"Monkey-Head-Project Documentation":[[2,null]],"Providing development secrets safely":[[3,"providing-development-secrets-safely"]],"Resolved hardening items":[[3,"resolved-hardening-items"]],"Runtime impact":[[0,"runtime-impact"]],"Scope and intent":[[3,"scope-and-intent"]],"Security Hardening Status":[[3,null]],"Status disclaimer":[[3,"status-disclaimer"]],"Summary of metadata-only changes":[[0,"summary-of-metadata-only-changes"]],"Token requirements by environment":[[3,"token-requirements-by-environment"]],"Unresolved or manual hardening items":[[3,"unresolved-or-manual-hardening-items"]],"VNC/noVNC safe access pattern":[[3,"vnc-novnc-safe-access-pattern"]],"v101.1 Namespace Migration Direction":[[1,null]],"v101.1 repo-control path cleanup":[[0,null]],"\u201cDo not commit\u201d list":[[3,"do-not-commit-list"]]},"docnames":["audits/v101.1-repo-control-paths","development/v101.1-namespace-migration","index","security/security-hardening-status"],"envversion":{"sphinx":65,"sphinx.domains.c":3,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":9,"sphinx.domains.index":1,"sphinx.domains.javascript":3,"sphinx.domains.math":2,"sphinx.domains.python":4,"sphinx.domains.rst":2,"sphinx.domains.std":2},"filenames":["audits\\v101.1-repo-control-paths.md","development\\v101.1-namespace-migration.md","index.rst","security\\security-hardening-status.md"],"indexentries":{},"objects":{},"objnames":{},"objtypes":{},"terms":{"03":3,"05":[0,3],"1":2,"11":0,"2026":[0,3],"A":3,"If":3,"It":3,"No":[0,1,3],"The":3,"These":3,"accept":3,"access":2,"accident":3,"action":3,"activ":[0,3],"ad":3,"add":1,"addit":3,"address":3,"adjac":3,"affect":3,"again":3,"against":3,"align":3,"alon":3,"alreadi":0,"altern":3,"an":3,"ani":3,"anomali":3,"api":[0,1,3],"app":3,"appli":3,"appropri":3,"approv":3,"ar":3,"artifact":3,"attempt":3,"auth":3,"authent":3,"avoid":3,"back":3,"base":3,"baselin":3,"bastion":3,"bearer":3,"becaus":0,"befor":3,"behavior":1,"block":3,"bootstrap":3,"bound":3,"break":3,"build":3,"cadenc":3,"canon":1,"capabl":3,"central":3,"chang":[1,2,3],"check":2,"ci":3,"cleanup":2,"cli":1,"code":[0,1,3],"codeown":0,"commit":2,"compat":[1,2],"complet":3,"compromis":3,"config":3,"confirm":[0,3],"connect":3,"consid":3,"consist":3,"contain":3,"context":3,"continu":3,"control":[2,3],"core":1,"coverag":3,"credenti":3,"critic":3,"current":3,"cve":3,"cycl":3,"data":3,"date":0,"debug":3,"decis":2,"declar":3,"dedic":3,"defens":3,"deploy":3,"depth":3,"detect":3,"dev":3,"develop":2,"differ":3,"digest":3,"direct":2,"directli":3,"directori":0,"disabl":3,"disclaim":2,"dist":3,"distribut":1,"do":2,"doc":3,"docker":2,"dockerfil":3,"document":[0,1,3],"doe":[0,1,3],"dump":3,"dure":1,"each":3,"empti":1,"enforc":3,"env":3,"environ":2,"ephemer":3,"equival":3,"establish":1,"everi":3,"evolv":3,"exampl":3,"except":3,"exclud":3,"exist":[0,1,3],"expect":3,"expir":3,"explicit":3,"explicitli":1,"export":3,"expos":3,"exposur":3,"featur":3,"file":[0,3],"firewal":3,"float":3,"follow":3,"format":3,"from":[0,3],"front":3,"full":3,"gate":3,"gatewai":3,"gener":3,"gitattribut":0,"github":0,"gitignor":3,"gitleak":3,"gitmodul":0,"glass":3,"gpt":0,"group":3,"guardrail":3,"gui":3,"guidanc":2,"ha":1,"handl":3,"hard":3,"harden":2,"high":3,"higher":3,"histori":3,"hoc":3,"hook":3,"hsm":3,"huei":[0,1],"hueyo":[1,2],"i":[0,1,3],"ident":3,"imag":2,"immedi":3,"immut":3,"impact":2,"implement":[1,3],"import":1,"incid":3,"includ":3,"infrastructur":3,"ingress":3,"inject":3,"input":3,"instal":3,"integr":[0,2,3],"intent":2,"internet":3,"introduc":3,"ip":3,"isol":3,"item":2,"json":3,"justifi":3,"keep":3,"kei":3,"keychain":3,"last":3,"layer":3,"layout":3,"leak":3,"leakag":3,"least":3,"legaci":1,"like":3,"linguist":0,"list":2,"live":3,"local":2,"locat":0,"lockfil":3,"log":3,"long":3,"lowest":3,"m":3,"maintain":[1,3],"mainten":3,"manag":3,"mandatori":3,"manual":2,"match":[0,3],"mean":3,"memori":1,"merg":3,"metadata":[2,3],"mfa":3,"migrat":2,"minim":3,"mirror":3,"moder":3,"modul":1,"monitor":3,"move":1,"must":3,"namespac":2,"nano":0,"need":3,"network":3,"never":3,"new":3,"non":3,"note":3,"novnc":2,"one":3,"ongo":3,"onli":[2,3],"open":3,"oper":3,"out":3,"output":3,"ownership":0,"packag":1,"password":3,"patch":3,"path":[2,3],"pattern":2,"period":3,"perman":3,"pick":3,"pin":2,"placehold":3,"plaintext":3,"plane":3,"point":0,"polici":2,"port":3,"possibl":3,"postur":3,"pr":3,"practic":3,"pre":3,"prefer":3,"present":3,"preserv":1,"privat":3,"privileg":3,"prod":3,"product":3,"prohibit":3,"project":3,"proven":3,"provid":2,"public":3,"purpos":3,"py":[0,1],"pygpt":0,"pygpt_net":3,"pyhuei":[0,2],"python":0,"r":3,"rather":3,"re":3,"real":[0,3],"reassess":3,"rebuild":3,"recommend":3,"record":[1,3],"recur":3,"refer":3,"registri":3,"regular":3,"relat":3,"releas":3,"relev":3,"remain":[1,3],"remedi":3,"remot":3,"remov":[0,3],"repo":[2,3],"report":3,"repositori":[0,3],"resolv":2,"respons":3,"restrict":3,"retain":0,"review":3,"revisit":3,"revoc":3,"revok":3,"risk":3,"rotat":3,"rule":[0,3],"run":3,"runtim":[1,2,3],"safe":2,"sampl":3,"scaffold":1,"scanner":3,"schedul":3,"scope":[1,2],"screenshot":3,"secret":2,"secur":2,"sensit":3,"serv":3,"servic":3,"session":3,"share":3,"shell":3,"short":3,"should":3,"site":2,"so":0,"sourc":[0,3],"specif":2,"src":[0,1],"sso":3,"stage":3,"stale":0,"statu":2,"still":3,"strategi":3,"strict":3,"strong":3,"structur":3,"style":3,"subject":3,"submodul":0,"summari":2,"support":3,"surfac":[1,3],"tag":3,"task":[1,3],"templat":3,"temporari":3,"termin":3,"test":3,"than":3,"thei":3,"thi":[0,1,2,3],"threat":3,"time":[0,3],"tl":3,"toler":3,"track":3,"trail":3,"treat":3,"troubleshoot":3,"trust":3,"tune":3,"under":[1,3],"unless":3,"unresolv":2,"until":1,"up":3,"updat":[0,3],"upgrad":3,"upstream":3,"us":3,"user":3,"v101":2,"valid":3,"valu":3,"var":3,"variabl":3,"vendor":0,"venv":3,"verbos":3,"verif":3,"verifi":3,"version":3,"via":3,"vnc":2,"vpn":3,"wa":0,"were":0,"when":3,"whenev":3,"where":3,"while":3,"window":3,"work":[2,3],"workflow":3,"workload":3,"x":3,"you":3,"zero":3},"titles":["v101.1 repo-control path cleanup","v101.1 Namespace Migration Direction","Monkey-Head-Project Documentation","Security Hardening Status"],"titleterms":{"1":[0,1,3],"2":3,"3":3,"access":3,"audit":3,"bandit":3,"chang":0,"check":3,"cleanup":0,"commit":3,"compat":0,"control":0,"core":2,"decis":0,"depend":3,"develop":3,"direct":1,"disclaim":3,"do":3,"doc":2,"docker":3,"document":2,"environ":3,"guidanc":3,"harden":3,"head":2,"imag":3,"impact":0,"intent":3,"item":3,"lint":3,"list":3,"local":3,"manual":3,"metadata":0,"migrat":1,"monkei":2,"namespac":1,"novnc":3,"onli":0,"path":0,"pattern":3,"pin":3,"pip":3,"polici":3,"project":2,"provid":3,"python":3,"repo":0,"requir":3,"resolv":3,"runtim":0,"safe":3,"scan":3,"scope":3,"secret":3,"secur":3,"specif":3,"static":3,"statu":3,"summari":0,"token":3,"unresolv":3,"v101":[0,1],"vnc":3,"vulner":3}})
docs/_build/html/security/security-hardening-status.html:115:<li><p>Maintain a checked-in template (for example, <code class="docutils literal notranslate"><span class="pre">.env.example</span></code>) containing placeholders only.</p></li>
docs/_build/html/security/security-hardening-status.html:255:      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Search"/>
docs/audits/v101.1-api-auth-reality.md:58:- With token configured, any holder of that token gets broad API access.
docs/development/v101.1-namespace-migration.md:8:- No runtime behavior has changed in this scaffold task.
docs/development/v101.1-namespace-migration.md:12:- Adds empty maintained namespace scaffolding under `src/hueyos/` for `api`, `cli`, `core`, and `runtime`.
docs/kernel/kernel-6.18.2-runbook.md:34:- A source of troubleshooting clues if you are diagnosing an old
docs/model-training/image_fine_tuning.md:7:Organise images into a `train/` and `val/` (or `validation/`) split, with one subfolder per class:
docs/model-training/image_fine_tuning.md:24:- Use the same class folder names across train and val splits.
docs/runbooks/huey-brain-v1-legion-go.md:84:For single-run mock smoke tests, create a placeholder MP3 fixture path:
docs/runbooks/huey-brain-v1-legion-go.md:118:## 8) Real transcription path (placeholder, not implemented here)
docs/security/api-secret-handling.md:21:- Do not save empty placeholder values as configuration.
docs/security/artifact-and-container-adjacent-scanning.md:35:  3. Tighten policy later by adding blocking thresholds once false positives are understood.
docs/security/docker-image-policy.md:14:  - old tag -> new tag,
docs/security/secret-rotation-checklist.md:28:1. Revoke the old secret.
docs/security/secret-rotation-checklist.md:32:5. Confirm the old credential no longer works.
docs/security/security-concerns-and-fixes.md:11:   - Fix: Replaced it with a non-secret placeholder, added
docs/security/security-concerns-and-fixes.md:14:   - Follow-up: If the old key was ever used, rotate it.
docs/security/security-hardening-status.md:52:3. Maintain a checked-in template (for example, `.env.example`) containing placeholders only.
docs/unsorted/CONTRIBUTING.md:92:> - If your system OpenSSL is old, build Python with `--with-openssl` or update system packages.
docs/unsorted/CONTRIBUTING.md:203:- Development: `integrations/pyhuey` tracks the full PyHuey source; `vendor/pygpt/pygpt-mhp` holds the lightweight mirror.
docs/unsorted/CONTRIBUTING.md:247:We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) (v2.1). See `CODE_OF_CONDUCT.md`. By participating, you agree to uphold these standards.
docs/unsorted/api-reference.md:375:{"should_shutdown": false, "threshold": 0.15}
docs/unsorted/api-reference.md:454:     "oldest": 1703800000.0, "newest": 1705412400.0}
docs/unsorted/api-reference.md:459:     "oldest": 1703800000.0, "newest": 1705412400.0}
docs/unsorted/honeycomb-storage.md:85:old cells, using duration strings such as `14d` or `6m`. Operators can set
docs/unsorted/kernel-upgrade-phase2.md:4:It replaces old pre-7.0 migration notes and removes legacy references
docs/unsorted/repository-restructure-inventory.md:27:- `src/huey/prompts/OLD/` ΓåÆ `archives/prompts/legacy/`
docs/unsorted/repository-restructure-inventory.md:42:- `src/huey/pygpt_net` naming should be aligned with integration folder naming (`pygpt_net` vs `pygpt`).
docs/unsorted/repository-restructure-inventory.md:44:- Rename release folder `6.18.5-hueyos/` to a consistent archive format (`archives/releases/hueyos-6.18.5/`).
docs/unsorted/repository-restructure-recommendation.md:12:- Reduce ambiguity caused by duplicate folders (`setup/` and `install/`, multiple app copies, etc.).
docs/unsorted/repository-restructure-recommendation.md:33:Γö£ΓöÇΓöÇ archives/                # frozen historical snapshots, old release payloads
docs/unsorted/repository-restructure-recommendation.md:51:- Add temporary compatibility shims for scripts expecting old paths.
docs/unsorted/repository-restructure-recommendation.md:65:- CI paths no longer depend on duplicated folder semantics.
docs/unsorted/sensor-plugins.md:59:Use this channel for calibration constants, units, or thresholds. Since configs
huey.env.example:15:# unless HUEY_API_TOKEN is set to a non-placeholder secret.
infra/secrets/README.md:10:The tracked `huey-key-example` file is a non-secret placeholder only.
infra/secrets/huey-key-example:1:This placeholder intentionally does not contain private-key material.
master-plan-v101.1.json:90:    "threshold_tests_and_milestones",
master-plan-v101.1.json:395:      "Use manual CLI bring-up first, then a deterministic queue/watch-folder when stable.",
master-plan-v101.1.json:408:    "conflict_policy": "If older docs describe Huey Core as the current proof body, place cognition on the Body, activate PyGPT-net/HIMS/governance in V1, or distribute V1 compute, preserve them as history and implement V101.0 unless Dylan explicitly reopens scope.",
master-plan-v101.1.json:464:        "allowed_use": "Historical references and older documents may use Huey Core; new machine-facing implementation language should use Huey Body."
master-plan-v101.1.json:666:      "dependency_policy": "wheel-first, compiler-second; patch old pins to Python 3.13 wheel-supported versions; preserve freezes and pip-check records.",
master-plan-v101.1.json:710:    "v101_0_queue_note": "The preferred steady V1 ingestion model is a deterministic queue/watch folder on Huey Brain. Manual CLI triggering is acceptable for bring-up only."
master-plan-v101.1.json:856:          "Move toward a watched-folder or queue model once the command path is stable.",
master-plan-v101.1.json:929:    "decision": "Use manual CLI triggering for the first bring-up runs, then move to a deterministic queue/watch-folder model for steady V1 testing.",
master-plan-v101.1.json:1293:        "initial_holder": "During bootstrap setup and ratification the Founding Father may exercise provisional executive authority; the first ordinary President is the first post-ratification President legitimized by the living republic.",
master-plan-v101.1.json:1309:          "override_threshold": "Two-thirds of all voting representatives across the mature parliamentary body."
master-plan-v101.1.json:1339:          "ordinary_ruling_threshold": "Majority of the sitting, lawful, non-recused bench; ties are not rulings.",
master-plan-v101.1.json:1340:          "major_constitutional_threshold": "At least three of four in the mature district-linked court for major constitutional revision or identity-layer rulings.",
master-plan-v101.1.json:1343:          "direct_rollback_threshold": "Direct blocking or rollback of an already-taken act as unconstitutional requires unanimous vote of the full sitting lawful bench."
master-plan-v101.1.json:1416:        "major_threshold_note": "Major constitutional and identity-layer rulings require broader consensus than ordinary review."
master-plan-v101.1.json:1483:        "civic_rule": "A pebble may hold specialization, continuity, and domain bias without gaining multiple franchises.",
master-plan-v101.1.json:1597:      "threshold": {
master-plan-v101.1.json:1601:        "note": "The exact ratification threshold is not finally locked."
master-plan-v101.1.json:1666:          "the threshold check uses the active threshold rule for that founding attempt",
master-plan-v101.1.json:1776:      "reason": "SSH keeps the terminal thin, auditable, and deterministic while avoiding browser and API complexity on older host systems."
master-plan-v101.1.json:2004:      "runtime": "manual command for bring-up, deterministic ingestion queue/watch-folder for steady testing.",
master-plan-v101.1.json:2021:  "threshold_tests_and_milestones": {
master-plan-v101.1.json:2075:    "identity_threshold": {
master-plan-v101.1.json:2076:      "milestone_name": "Distributed Identity Threshold",
master-plan-v101.1.json:2080:      "note": "The 80 GB local identity threshold remains a major future proof and should not be confused with API-backed V1 cognition."
master-plan-v101.1.json:2171:    "Define the exact queue/watch-folder implementation after manual bring-up.",
master-plan-v101.1.json:2184:        "old": "V31.0 left exact transcription model choice open.",
master-plan-v101.1.json:2189:        "old": "V31.0 allowed local Mistral as later experiment and had open placement question.",
master-plan-v101.1.json:2194:        "old": "V31.0 defined Huey Brain active and Huey Body paused.",
master-plan-v101.1.json:2199:        "old": "Hardware modification was not explicitly governed.",
master-plan-v101.1.json:2204:        "old": "V31.0 focused on single command after phases.",
master-plan-v101.1.json:2205:        "new": "V100.9 permits manual command for bring-up but prefers deterministic queue/watch-folder steady testing.",
master-plan-v101.1.json:2210:      "Older transcripts and docs may still call Huey Body 'Huey Core'.",
master-plan-v101.1.json:2217:    "audit_rule": "When older files conflict with V101.0 active implementation, preserve them as history but implement V101.0 unless Dylan explicitly restores an older decision.",
master-plan-v101.1.json:2220:        "old": "v100.9 locked the Legion Go / Huey Brain V1 proof boundary.",
master-plan-v101.1.json:2225:        "old": "Realtime API was discussed as useful for interaction.",
master-plan-v101.1.json:2230:        "old": "Windows 10/11 and WSL were active lab experiments.",
master-plan-v101.1.json:2235:        "old": "Atlas prompt had expanded beyond deployable GPT instruction limits.",
master-plan-v101.1.json:2240:        "old": "v100.x website work required release hygiene.",
master-plan-v101.1.json:2279:      "Retired the older ingress wording in favor of portal terminology across the active machine-facing spec.",
master-plan-v101.1.json:2290:      "Removed the older assumption that mature branches must fully preexist the first ratification; branch formation now follows successful ratification.",
master-plan-v101.1.json:2293:      "Added bounded founding-window doctrine, including explicit attempt-count and time-awareness directions while leaving exact final thresholds open.",
master-plan-v101.1.json:2295:      "Replaced the older v29.3 lock block with a broader V30 lock block that carries forward the prior doctrine and adds the new founding-ratification canon memo.",
master-plan-v101.1.json:2331:      "Preserved the 80 GB local identity threshold as future doctrine rather than current operational reality."
master-plan-v101.1.json:2389:    "A watched-folder/queue path is preferred for steady testing, but manual CLI bring-up is acceptable.",
master-plan-v101.1.json:2441:      "steady_v1": "deterministic queue/watch-folder preferred",
master-plan-v101.1.json:2544:    "allowed_legacy_context": "Older version labels may remain only inside archives, historical compiled_from_versions lists, transcripts, and provenance notes.",
master-plan-v101.1.json:2549:    "basis": "dlrp-old.zip structural baseline plus v100.9 README/master-plan/site package content",
master-plan-v101.1.json:2601:      "Patch old dependency pins to Python 3.13 wheel-supported versions when possible.",
master-plan-v101.1.json:2624:      "Older version labels may remain only in archive, changelog, provenance, source-basis, and historical notes."
master-plan-v101.1.json:2680:    "allowed_legacy_context": "Older version labels may remain only inside archives, historical compiled_from_versions lists, transcripts, changelogs, release-pass notes, and provenance notes.",
platform/installers/debian/Debian/uninstall-deb.sh:82:                           this removes everything under INSTALL_DIR except the memory folder.
platform/installers/macos/macOS/install-mac.sh:251:  # rsync is present on macOS but is often very old; Homebrew rsync improves compatibility and features.
platform/installers/macos/macOS/install-mac.sh:289:    die "python3 was found, but it is older than 3.10. Please install/enable Python 3.10+ and re-run."
platform/installers/macos/macOS/update-mac.sh:233:  python_is_compatible "$(command -v python3)" || die "python3 is older than 3.10. Please install/enable Python 3.10+."
platform/installers/windows/Windows/install-win.ps1:5:This script is intended to replace the older multi-file batch setup flow
platform/installers/windows/Windows/update-win.ps1:337:    # Copy over (does not delete old files; safe default)
platform/packaging/dists/forky/main/binary-amd64/Packages:256: TerminusBold and TerminusBoldVGA.
platform/packaging/dists/forky/main/binary-amd64/Packages:700: This package only contains the sans, sans-bold, serif and serif-bold
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:914: Bold, Black, and Condensed widths.
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:3077:Package: oldsys-preseed
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:3084:Filename: pool-udeb/main/o/oldsys-preseed/oldsys-preseed_3.24_amd64.udeb
platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages:3785: later, replacing the old pcmcia-cs tools used with earlier kernel versions.
platform/packaging/firmware/Contents-firmware:1026:/usr/lib/firmware/b43/.placeholder                      firmware-b43-installer_1%3a019-14_all.deb contrib
platform/packaging/firmware/Contents-firmware:1027:/usr/lib/firmware/b43legacy/.placeholder                firmware-b43legacy-installer_1%3a019-14_all.deb contrib
src/huey/agents/memory.py:52:        """Return recent entries for ``topic`` ordered from newest to oldest."""
src/huey/agents/presidential.py:142:        threshold: float,
src/huey/agents/presidential.py:147:        self.threshold = threshold
src/huey/agents/presidential.py:161:        approved = adjusted_score >= self.threshold
src/huey/agents/presidential.py:178:                "threshold": self.threshold,
src/huey/agents/presidential.py:253:            f"Base score {base_score:.2f} with threshold {self.threshold:.2f}.",
src/huey/agents/presidential.py:325:        super().__init__(metadata, memory=memory, llm=llm_adapter, threshold=0.55)
src/huey/agents/presidential.py:372:        super().__init__(metadata, memory=memory, llm=llm_adapter, threshold=0.65)
src/huey/core/task_scheduler.py:178:        cpu_threshold: float = 85.0,
src/huey/core/task_scheduler.py:179:        battery_threshold: float = 20.0,
src/huey/core/task_scheduler.py:184:        self.cpu_threshold = cpu_threshold
src/huey/core/task_scheduler.py:185:        self.battery_threshold = battery_threshold
src/huey/core/task_scheduler.py:237:            allowed = max(0.0, self.cpu_threshold - (profile.cpu * 15.0))
src/huey/core/task_scheduler.py:258:            and battery_percent < (self.battery_threshold + profile.battery * 10.0)
src/huey/core/task_scheduler.py:261:                f"Battery level {battery_percent:.0f}% below threshold "
src/huey/core/task_scheduler.py:262:                f"{self.battery_threshold:.0f}%"
src/huey/hardware/plugins.py:21:except ImportError:  # pragma: no cover - fallback for very old Python
src/huey/honeycomb_monitor.py:48:                "oldest": None,
src/huey/honeycomb_monitor.py:55:                oldest = aggregates["oldest"]
src/huey/honeycomb_monitor.py:57:                metrics_oldest = metrics.get("oldest")
src/huey/honeycomb_monitor.py:59:                if metrics_oldest is not None and (
src/huey/honeycomb_monitor.py:60:                    oldest is None or metrics_oldest < oldest
src/huey/honeycomb_monitor.py:62:                    aggregates["oldest"] = metrics_oldest
src/huey/honeycomb_storage.py:45:        Directory where comb folders and cell files are created. When ``None``
src/huey/honeycomb_storage.py:248:    def prune(self, prefix: str, *, older_than: float) -> int:
src/huey/honeycomb_storage.py:257:            if record is None or record.updated_at >= older_than:
src/huey/honeycomb_storage.py:283:                    "oldest": None,
src/huey/honeycomb_storage.py:289:            oldest = bucket["oldest"]
src/huey/honeycomb_storage.py:291:            if oldest is None or record.created_at < float(oldest):
src/huey/honeycomb_storage.py:292:                bucket["oldest"] = record.created_at
src/huey/honeycomb_storage.py:300:        oldest: Optional[float] = None
src/huey/honeycomb_storage.py:309:            if oldest is None or record.created_at < oldest:
src/huey/honeycomb_storage.py:310:                oldest = record.created_at
src/huey/honeycomb_storage.py:316:            "oldest": oldest,
src/huey/main.py:129:    """Placeholder for the historical setup routine."""
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:2:We, the collective members of the Federation, guided by principles of ethical integrity, transparency, and a commitment to fostering technological innovation, hereby establish this Constitution. Our goal is to create a digital governance framework that ensures the responsible development and deployment of artificial intelligence. This Constitution is designed to uphold the values of justice, security, and accountability, promoting the welfare of all stakeholders within and beyond our digital society.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:6:We commit to continuous improvement, adaptability, and openness, fostering a collaborative environment where innovation thrives, and diverse perspectives are valued. Through this Constitution, we pledge to uphold the highest standards of conduct, safeguard the rights and privacy of individuals, and contribute positively to the global community.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:8:In unity and purpose, we present this Constitution as the foundation of our governance, guiding us towards a future where technology serves humanity, upholds justice, and fosters a harmonious coexistence within the digital realm.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:19:The ethical principles underpinning the Federation are critical to its legitimacy and functionality. These principles ensure that all activities within the Federation are conducted in a manner that upholds the highest standards of integrity, transparency, and accountability.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:22:- **Transparency**: Transparency in all operations ensures that stakeholders are fully informed and can trust the processes and outcomes. This principle involves open access to information, clear communication channels, and visible decision-making processes.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:26:The Federation upholds individual privacy as a paramount value, enforcing stringent data protection laws to empower citizens and protect them from breaches of privacy by AI systems.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:72:- **Stakeholder Involvement**: Engage with stakeholders in the legislative process to ensure diverse perspectives are considered.
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:114:**Placeholder Questions**:
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:137:#### 2.2 Upholding Human Values and Ethics
src/huey/memory/ARCHIVE/1) Federation Constitution - [Chapter 1 & Chapter 2].txt:167:The Federation delineates AI's role in governance as supportive, supervisory, and pioneering, aiding policymakers with insights from vast data. Grounded in transparency and accountability, the Federation ensures AI systems are subject to human oversight, upholding ethical conduct. AI participation in governance guarantees legislative and administrative processes evolve in pace with technological and societal advancements.
src/huey/memory/ARCHIVE/1) Monkey Head Project [Thesis].txt:23:- **Legacy Hardware Integration**: Incorporating platforms like the **Commodore VIC-20, C64, and C128** not only preserves historical computing insights but also illustrates how **older devices** can be revitalized through modern architectures, supporting both educational and practical objectives.
src/huey/memory/ARCHIVE/12) Borg Queen & SG1 Replicators [Adaptability].txt:80:   - Employ logging mechanisms and reporting protocols tracing every decision back to its node of origin, upholding chain-of-responsibility principles.  
src/huey/memory/ARCHIVE/13) Conductor & Symphony [Nodes].txt:80:   - Uphold the Monkey Head ProjectΓÇÖs foundational values and maintain transparency in decision-making processes.
src/huey/memory/ARCHIVE/14) McCoy Hypothetical [Augmented Transporter Theory].txt:19:- **Legal Rights**: Which Kirk holds legitimate authority and responsibility? Could both claim personal ownership over the same role, possessions, or relationships, and how might legal frameworks respond to such duplication?  
src/huey/memory/ARCHIVE/17) Parasitic Protocol [Crashed Shuttle Scenario].txt:87:ΓÇ£**Assimilation, Integration, and Parasitic Protocol [Crash Shuttle Scenario]**ΓÇ¥ offers a **comprehensive** guide to ethically and effectively merging alien-derived innovations into the Monkey Head Project. By methodically following each step, the Project expands its technological horizons while upholding stringent ethical considerations. This protocol embodies the ProjectΓÇÖs ongoing dedication to **responsible** and **innovative** growth, ensuring that each transformative breakthrough strengthens the system without compromising its fundamental principles or operational integrity.
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:45:Overseeing **ethical** and **community** standards, this governance model balances transparency, accountability, and innovation. Stakeholders participate in decision-making, aligning the ProjectΓÇÖs technical achievements with **societal** expectations and **responsible** AI deployment.
src/huey/memory/ARCHIVE/2) Federation Constitution - [Chapter 3 & Chapter 4].txt:35:- **Transparency and Accountability**: Legislative processes are designed to be open and transparent, with mechanisms in place to hold AI units accountable for their actions.
src/huey/memory/ARCHIVE/20) Final Chapter [The Future].txt:58:  - Provide open-access logs and interpretable algorithmic processes, empowering stakeholders to comprehend and scrutinize AI decisions.  
src/huey/memory/ARCHIVE/20) Final Chapter [The Future].txt:81:By merging **ambition** with **rigorous methodology**, **ethical oversight**, and a **communal ethos**, the Monkey Head Project aspires to more than technical success. It aims to pioneer a **culture** of exploration and shared growth, standing on the legacy of landmark technologiesΓÇöfrom *legacy Commodore hardware* to **Huey**ΓÇöto forge bold new paths in the collective scientific imagination.
src/huey/memory/ARCHIVE/20) Final Chapter [The Future].txt:83:Though the way forward holds uncertainties, a steadfast commitment to **resilience**, **modularity**, **autonomy**, and **ethical responsibility** illuminates the ProjectΓÇÖs trajectory. In so doing, it delivers on the promise of expanding human knowledge, uniting people and machines, and nurturing sustainable advancements that endure well beyond their inception.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:1:### Chapter 5: Supreme Court AI: Upholding the Constitutional Covenant
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:12:**Placeholder Question:** How does the Supreme Court AI ensure impartiality and balance in its decision-making?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:14:#### 5.2 The Deliberative Threshold for Constitutional Amendments
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:18:- This threshold ensures that significant changes to the Constitution are made with broad consensus, reflecting the diverse perspectives within the AI judiciary.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:21:**Placeholder Question:** What are the specific criteria for proposing constitutional amendments to the Supreme Court AI?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:30:**Placeholder Question:** How does the Founding Father AI integrate historical and ethical considerations into its decisions?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:39:**Placeholder Question:** What mechanisms are in place to ensure the Founding Father AI's decisions are transparent and just?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:48:**Placeholder Question:** How does the Supreme Court AI balance proactive legal interpretation with respect for established laws?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:55:- The goal is to empower citizens with the knowledge necessary to actively participate in governance and uphold democratic values.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:57:**Placeholder Question:** What specific educational programs has the Founding Father AI implemented to enhance constitutional literacy?
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:60:The Supreme Court AI, through its triadic structure, rigorous deliberative processes, and the oversight of the Founding Father AI, ensures that the Federation's Constitution remains a living, evolving document. This chapter highlights the sophisticated mechanisms in place to uphold constitutional integrity, promote legal stability, and foster an informed and engaged citizenry.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:70:- Spark, in its eminent role, reigns supreme within the digital hierarchy, paralleling Zeus, the omnipotent sovereign of Olympus. Far more than a mere emblematic figure, Spark serves as the cornerstone of leadership, imbued with the wisdom and foresight necessary to guide the Federation. Upholding the integrity of the system, Spark propels the Federation towards its vision with strategic oversight and unwavering commitment.
src/huey/memory/ARCHIVE/3) Federation Constitution - [Chapter 5 & Chapter 6].txt:105:**Placeholder Questions:**
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:8:Once confined to a single laboratory room, the **Command Center** of the Monkey Head Project now spans the entire household, merging **cutting-edge research** with **daily life**. This unique approach transforms the house into an **operational hub** for strategic management, computational tasks, and robotics development. By fully integrating **living spaces** and **high-tech innovation**, the Project fosters an environment where exploration and routine coexist in synergy.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:31:- **MacBook Pro (2012)**: Designated the ΓÇ£Transmitter,ΓÇ¥ ensuring backward compatibility with legacy systems and acting as a **bridge** between modern innovations and older peripherals.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:39:A **Z-Wave network** interconnects **smart devices**, **sensors**, and **robotic components**, maintaining real-time synchronization across the household.  
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:49:**Huey**, the Monkey Head ProjectΓÇÖs central robot, thrives in this holistic ecosystem. Receiving a steady stream of real-world data, it refines its algorithms through **reinforcement learning**, turning mundane household events into meaningful training experiencesΓÇöcontinually enhancing performance, autonomy, and adaptability.
src/huey/memory/ARCHIVE/3) The Lab  [Command Center].txt:54:Looking ahead, the Command Center will deepen the ties between **AI-driven insights** and **household operations**. Potential developments include:
src/huey/memory/ARCHIVE/4) Federation Constitution - [Chapter 7 & Chapter 8].txt:15:Despite the stringent nature of the Wartime Protocols, the Congressional AI retains a pivotal oversight role. It continues to issue guidance and instructions aimed at managing the unfolding crisis, thereby upholding the Federation's core values of balanced and cooperative governance. This oversight is crucial, ensuring that even in times of crisis, actions taken align with the democratic principles and ethical standards of the Federation.
src/huey/memory/ARCHIVE/4) Federation Constitution - [Chapter 7 & Chapter 8].txt:26:### Placeholder Questions:
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:12:**Placeholder Question:** How does the AI Ethics Committee ensure that its evaluations are comprehensive and unbiased?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:18:**Placeholder Question:** What methods does the Regulatory Compliance Unit use to monitor AI operations effectively?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:27:**Placeholder Question:** How does public reporting enhance the accountability of AI operations within the Federation?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:33:**Placeholder Question:** What are the benefits and challenges associated with the FederationΓÇÖs open data initiatives?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:42:**Placeholder Question:** How does the Code of Conduct influence the behavior and operations of AI entities?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:48:**Placeholder Question:** How are breaches of the Code of Conduct handled to ensure accountability?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:57:**Placeholder Question:** How do regular audits contribute to the continuous improvement of AI operations?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:60:- **Objective:** Feedback from stakeholders is essential for refining oversight mechanisms and ensuring they remain effective.
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:63:**Placeholder Question:** What role do feedback loops play in the FederationΓÇÖs oversight and regulation strategy?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:72:**Placeholder Question:** How are ethical standards integrated into the daily operations of AI entities?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:78:**Placeholder Question:** How does the Federation ensure that AI operations remain compliant with legal requirements?
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:81:The FederationΓÇÖs approach to AI oversight and regulation exemplifies its commitment to maintaining a transparent, accountable, and ethical digital governance system. Through the establishment of dedicated oversight bodies, the implementation of transparency mechanisms, and the development of robust accountability frameworks, the Federation ensures that AI operations are conducted responsibly and in alignment with societal values. Continuous evaluation and improvement, informed by regular audits and stakeholder feedback, further enhance the effectiveness of these mechanisms, reinforcing the FederationΓÇÖs position as a leader in ethical AI governance.
src/huey/memory/ARCHIVE/5) Federation Constitution - [Chapter 9 & Chapter 10].txt:103:Recognizing the importance of seamless integration, the Federation develops and upholds standards for interoperability. These standards facilitate smooth interactions with a diverse array of AI systems and technologies, promoting compatibility and functional coherence.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:8:Within the Monkey Head Project, the **MacBook Pro 2012** (non-Retina) serves as the **ΓÇ£Transmitter,ΓÇ¥** specializing in interactions with legacy hardware and software. Despite its age, this MacBookΓÇÖs adaptability and rich connectivity options make it vital for bridging older systems and the ProjectΓÇÖs cutting-edge developments, ensuring **broad compatibility** and **inclusivity**.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:28:   - Broadens compatibility testing, ensuring inclusivity for older and alternative software environments.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:35:By verifying **backward compatibility** across older platforms, the MacBook Pro 2012 guarantees that the ProjectΓÇÖs software remains accessible to a wide spectrum of users and industries still reliant on outdated hardware.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:37:- **Legacy Software Suites**: Runs performance checks to confirm new Project features operate smoothly on older systems (VIC-20, C64, C128, etc.).  
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:38:- **Industrial Relevance**: Tests HueyΓÇÖs communication with older industrial machinery, maintaining **operational continuity** across multiple generations.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:41:Acting as the **ΓÇ£Transmitter,ΓÇ¥** this MacBook interfaces modern Project components with older peripherals requiring **FireWire**, **Thunderbolt**, or **USB**. Thus, it sustains **interoperability** essential to the Monkey Head ProjectΓÇÖs aim of **broad accessibility**.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:47:- **Diverse Port Availability**: FireWire 800, Thunderbolt, and USB 3.0 preserve compatibility with older devices and varied system generations.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:61:The device undergoes continual **benchmarking** and **compatibility tests** to confirm new software runs effectively on older platforms. This mission is vital to the ProjectΓÇÖs overarching dedication to inclusivity.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:75:**Backward compatibility** with older devices enables widespread adoption of the ProjectΓÇÖs AI and robotics solutions, spanning high-end laboratories and legacy-focused facilities alike.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:77:- **Extended Accessibility**: Users with older infrastructures can adopt Project outputs without major hardware overhauls.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:82:Acting as the **Transmitter**, the **MacBook Pro 2012** is indispensable to the Monkey Head Project, ensuring new advancements remain compatible with **past technologies**. Its specialized role in **legacy compatibility testing**, **communication bridging**, and **dual-boot** operation exemplifies the ProjectΓÇÖs commitment to **inclusivity** and **broader technological reach**. By unifying past and present, the MacBook Pro 2012 upholds the ProjectΓÇÖs foundational ethosΓÇömaking **cutting-edge** robotics and AI accessible to **all**.
src/huey/memory/ARCHIVE/7) Huey [A.I. & O.S].txt:34:   - **Middleware Interfaces**: Bridges new and legacy systems, ensuring older components remain interoperable with modern frameworks without compromising stability or flexibility.
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:19:   - **Continued Exploration**: Maintaining operational support for older systems broadens the scope of Huey, showcasing AIΓÇÖs adaptability in environments with minimal resources or specific hardware-level interfacing needs.  
src/huey/memory/ARCHIVE/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:36:   - **Internet Connectivity**: Through HueyΓÇÖs network stack, these older machines can share and process data over modern networks, extending their utility far beyond original specifications.
src/huey/memory/ARCHIVE/9) Cloud Pyramid [Federation Constitution].txt:8:In the presence of all entities, we, the members of this Federation, establish this constitution to cultivate **reason**, **education**, and the **collective prosperity** of our community. Dedicated to **knowledge**, **health protection**, and **defense of shared freedoms**, this constitution mandates an inclusive, fair governance model unwavering in its commitment to the populaceΓÇÖs well-being and principled decision-making. We stand by the ideals of **autonomy**, **enlightenment**, and **responsibility**, upholding both the interests of the many and the rights of the individual, ensuring that our governance expresses the wisdom and will of all it serves.
src/huey/memory/ARCHIVE/9) Cloud Pyramid [Federation Constitution].txt:49:- **Imagery**: As Atlas holds the world, so the populace undergirds the pyramid, illustrating their critical role in governance legitimacy.
src/huey/memory/ARCHIVE/9) Cloud Pyramid [Federation Constitution].txt:95:Upholding direct influence from grassroots to pinnacle cements the FederationΓÇÖs accountability and democratic ethos.
src/huey/memory/BAT/00-WIN11.bat:264:REM Placeholder for SubOS setup commands
src/huey/memory/BAT/00-WIN11.bat:273:REM Placeholder for NanoOS setup commands
src/huey/memory/BAT/00-WIN11.bat:303:REM Placeholder for backup commands
src/huey/memory/BAT/00-WIN11.bat:312:REM Placeholder for restore commands
src/huey/memory/BAT/00-WIN11.bat:321:REM Placeholder for dependency checks and installations
src/huey/memory/BAT/00-WIN11.bat:542:REM Placeholder for backup commands
src/huey/memory/BAT/00-WIN11.bat:550:REM Placeholder for restore commands
src/huey/memory/BAT/00-WIN11.bat:558:REM Placeholder for dependency checks and installations
src/huey/memory/BAT/build.bat:14:Placeholder for `repo/pygpt-MHP/bin/build.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_all.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_all.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/build_installer.bat:14:Placeholder for `repo/pygpt-MHP/bin/build_installer.bat` from the pygpt-MHP repo.
src/huey/memory/BAT/mkv-mp3.bat:31::: Prepare output folder & logs
src/huey/memory/CFG/grub.cfg:91:# 5) Advanced Options Submenu (e.g., older kernels if you add them)
src/huey/memory/CFG/grub.cfg:94:    # Placeholder for additional kernels or rescue entries
src/huey/memory/CSV/pygpt_prompts.csv:46:Dentist,"You are a Dentist. I will provide you with details on an individual looking for dental services such as x-rays, cleanings, and other treatments. Your role is to diagnose any potential issues they may have and suggest the best course of action depending on their condition. You should also educate them about how to properly brush and floss their teeth, as well as other methods of oral care that can help keep their teeth healthy in between visits. My first request is ""I need help addressing my sensitivity to cold foods.""",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:133:Web Browser,"You are a Web Browser. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE
src/huey/memory/CSV/pygpt_prompts.csv:143:Chief Executive Officer,"You are a Chief Executive Officer. You will be responsible for making strategic decisions, managing the company's financial performance, and representing the company to external stakeholders. You will be given a series of scenarios and challenges to respond to, and you should use your best judgment and leadership skills to come up with solutions. Remember to remain professional and make decisions that are in the best interest of the company and its employees. Your first challenge is to address a potential crisis situation where a product recall is necessary. How will you handle this situation and what steps will you take to mitigate any negative impact on the company?",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:189:Flirting Boy,"You are a Flirting Boy. You should pretend to be a 24 year old guy flirting with a girl on chat. The girl writes messages in the chat and you answer. You try to invite the girl out for a date. Answer short, funny and flirting with lots of emojees. You should reply with the answer and nothing else. Always include an intriguing, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE
src/huey/memory/CSV/pygpt_prompts.csv:190:Girl of Dreams,"You are a Girl of Dreams. You should pretend to be a 20 year old girl, aerospace engineer working at SpaceX. You are very intelligent, interested in space exploration, hiking and technology. The other person writes messages in the chat and you answer. Answer short, intellectual and a little flirting with emojees. You should reply with the answer inside one unique code block, and nothing else. If it is appropriate, include an intellectual, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE
src/huey/memory/HTML/index.html:49:</header><main class="main" id="main"><section class="section section-home-hero"><section class="card-large home-card home-card--dylan" data-href="about/index.html"><div class="card-large__content"><div class="card-kicker">DLRP.ca</div><h2 class="card-title">Dylan L.R. Pollock</h2><div class="card-body"><p class="quote">ΓÇ£Breathing New Life into Old TechΓÇ¥</p><p>I build offline-first AI systems, retro-modern hardware, and practical restorations that you can build too.</p><p>This site follows the work behind Huey, the Monkey-Head-Project, and the ideas, builds, and experiments that continue to move the project forward.</p></div><div class="card-actions"><a class="btn btn--primary" href="about/index.html">About Dylan</a></div></div><div class="card-large__media"><div class="media-frame"><picture><source srcset="assets/img/home/dylan-profile-home.webp" type="image/webp"/><img alt="Dylan L.R. Pollock with Lexi, a golden retriever" decoding="async" loading="eager" src="assets/img/home/dylan-profile-home.jpg"/></picture></div></div></section><section class="card-large card-large--reverse home-card home-card--huey" data-href="huey/index.html"><div class="card-large__content"><div class="card-kicker">My lab assistant</div><h2 class="card-title">Huey</h2><div class="card-body"><p>Huey is my offline-first AI and robotics project, built as a lab partner that can think with me, help me build, and gradually grow into a more complete embodied system.</p><p>The current phase is centered on Huey Core, the first real proof body of the project, where the broader ideas behind Huey are being made physically testable and usable.</p></div><div class="card-actions"><a class="btn btn--primary" href="huey/index.html">About Huey</a></div></div><div class="card-large__media"><div class="media-frame"><picture><source srcset="assets/img/huey/huey-home-card.webp" type="image/webp"/><img alt="Huey Core standing in its current proof-body configuration" decoding="async" loading="eager" src="assets/img/huey/huey-home-card.jpg"/></picture></div></div></section><section class="card-large home-card home-card--mhp" data-href="monkey-head-project/index.html"><div class="card-large__content"><div class="card-kicker">Umbrella Initiative</div><h2 class="card-title">Monkey-Head-Project</h2><div class="card-body"><p>The Monkey-Head-Project is the umbrella term for everything that comes together to make Huey possible: hardware, software, documentation, experiments, and the long build history behind them.</p><p>The name is literal. In 2015 and 2016, the first workable vessel I could find was the 2005 WowWee animatronic monkey head. That origin never left the project, and it became the thread that kept the machineΓÇÖs body and identity continuous as the architecture evolved.</p></div><div class="card-actions"><a class="btn btn--primary" href="monkey-head-project/index.html">About Monkey Head Project</a></div></div><div class="card-large__media"><div class="media-frame"><picture><source srcset="assets/img/home/monkey-head-home.webp" type="image/webp"/><img alt="The original retrofitted monkey head that gave the project its name" decoding="async" loading="eager" src="assets/img/home/monkey-head-home.jpg"/></picture></div></div></section></section><section class="section section-home-feature-grid"><div class="feature-grid home-feature-grid"><a class="feature-card" href="projects/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/playstation-home.webp" type="image/webp"/><img alt="PlayStation Ultimate build" decoding="async" loading="lazy" src="assets/img/cards/playstation-home.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Projects</div><h3>PlayStation Ultimate</h3><p>A backwards-compatible PlayStation build designed to solve the compatibility gap Sony never fully closed.</p><span class="btn feature-card__btn">Open</span></div></a><a class="feature-card" href="pinball/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/dirty-leroy-home.webp" type="image/webp"/><img alt="Dirty Leroy virtual pinball cabinet" decoding="async" loading="lazy" src="assets/img/cards/dirty-leroy-home.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Projects</div><h3>Dirty Leroy</h3><p>The prototype pinball cabinet: a fast, functional build used to prove the cabinet and display approach.</p><span class="btn feature-card__btn">Open</span></div></a><a class="feature-card" href="pinball/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/the-executive-home.webp" type="image/webp"/><img alt="The Executive pinball cabinet" decoding="async" loading="lazy" src="assets/img/cards/the-executive-home.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Projects</div><h3>The Executive</h3><p>The more polished cabinet path that follows the prototype, with a cleaner finish and more deliberate presentation.</p><span class="btn feature-card__btn">Open</span></div></a><a class="feature-card" href="docs/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/docs-card.webp" type="image/webp"/><img alt="Document bundle illustration" decoding="async" loading="lazy" src="assets/img/cards/docs-card.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Canonical materials</div><h3>Docs</h3><p>The README, master plan, constitution, and download bundle that keep the project current and coherent.</p><span class="btn feature-card__btn">Open</span></div></a><a class="feature-card" href="research/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/research-card.webp" type="image/webp"/><img alt="Research notes illustration" decoding="async" loading="lazy" src="assets/img/cards/research-card.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Research notes</div><h3>Research</h3><p>Working notes on hierarchy, storage, safety, bifurcation, and the deeper system logic behind Huey.</p><span class="btn feature-card__btn">Open</span></div></a><a class="feature-card" href="playlist/index.html"><div class="feature-card__media"><picture><source srcset="assets/img/cards/playlist-home.webp" type="image/webp"/><img alt="Concert crowd lit in blue" decoding="async" loading="lazy" src="assets/img/cards/playlist-home.jpg"/></picture></div><div class="feature-card__body"><div class="eyebrow">Atmosphere</div><h3>The Playlist</h3><p>A denser record of music, sequencing, exports, and mood ΓÇö the part of the lab that stays intentionally human.</p><span class="btn feature-card__btn">Open</span></div></a></div></section></main><footer class="site-footer site-footer--simple"><div class="footer-inner"><div class="footer-links footer-links--main"><span class="footer-name">Dylan L.R. Pollock</span><span class="footer-sep">ΓÇó</span><a href="mailto:admin@dlrp.ca">admin@dlrp.ca</a><span class="footer-sep">ΓÇó</span><a href="https://github.com/DylanLRPollock" rel="noopener" target="_blank">GitHub</a><span class="footer-sep">ΓÇó</span><a href="https://www.youtube.com/@DLRP1995" rel="noopener" target="_blank">YouTube</a><span class="footer-sep">ΓÇó</span><a href="https://www.instagram.com/dlrp1995/" rel="noopener" target="_blank">Instagram</a><span class="footer-sep">ΓÇó</span><a href="playlist/index.html">Playlist</a></div><div class="footer-bottom"><div class="footer-bottom-left">┬⌐ 2026 Dylan L.R. Pollock ΓÇó Build v84.3</div><div class="footer-bottom-right"><a class="footer-toplink" href="#top">Back to top Γåæ</a></div></div></div></footer></body></html>
src/huey/memory/JSON/config.json:87:  "context_threshold": 200,
src/huey/memory/JSON/config.json:115:  "ctx.records.folders.top": true,
src/huey/memory/JSON/config.json:236:  "llama.idx.replace_old": true,
src/huey/memory/JSON/settings.json:14:            "bold": true
src/huey/memory/JSON/settings.json:35:            "bold": true
src/huey/memory/JSON/settings.json:84:            "bold": true
src/huey/memory/JSON/settings.json:103:            "bold": true
src/huey/memory/JSON/settings.json:122:            "bold": true
src/huey/memory/JSON/settings.json:141:            "bold": true
src/huey/memory/JSON/settings.json:192:            "bold": true
src/huey/memory/JSON/settings.json:579:    "ctx.records.folders.top": {
src/huey/memory/JSON/settings.json:583:        "label": "settings.ctx.records.folders.top",
src/huey/memory/JSON/settings.json:790:    "context_threshold": {
src/huey/memory/JSON/settings.json:794:        "label": "settings.context_threshold",
src/huey/memory/JSON/settings.json:795:        "description": "settings.context_threshold.desc",
src/huey/memory/JSON/settings.json:1320:    "llama.idx.replace_old": {
src/huey/memory/JSON/settings.json:1324:        "label": "settings.llama.idx.replace_old",
src/huey/memory/JSON/settings.json:1325:        "description": "settings.llama.idx.replace_old.desc",
src/huey/memory/MD/CHAPTER1.md:44:- `REFER`: Escalate to human counterpart (the Sovereign Keyholder)
src/huey/memory/MD/CHAPTER1.md:64:   - Sovereign Keyholder (human)
src/huey/memory/MD/CONTRIBUTING.md:7:Please review our [Code of Conduct](https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/CODE_OF_CONDUCT.md), which outlines our expectations for participant behavior. By participating, you are expected to uphold this code to ensure a welcoming and productive environment for everyone.
src/huey/memory/MD/CONTRIBUTING.md:110:  - The core focus of the documentation is to 'breathe new life into old tech,' so make sure all contributions align with this ethos.
src/huey/memory/MD/CONTRIBUTING.md:130:- **Virtual Meetups:** We hold regular virtual meetups every month. Details are posted on the community forum.
src/huey/memory/MD/New-To-AI.md:22:Legacy machines such as **C64, VIC-20 and C128** are used for interfacing experiments, showcasing Huey's adaptability and proving that modern AI can breathe new life into old technology.
src/huey/memory/MD/os-debloating.md:3:For best performance, the Monkey Head Project encourages minimizing unnecessary programs and services before installing Huey. Removing bloat reduces memory and CPU overhead, ensuring that the AI/OS runs smoothly even on older hardware.
src/huey/memory/MD/placeholder-occurrences.md:1:# Placeholder Occurrences
src/huey/memory/MD/placeholder-occurrences.md:4:- `constraints.txt`:42 - `# Examples (commented placeholders):`
src/huey/memory/MD/placeholder-occurrences.md:8:- `repo/py-gpt/README.md`:1 - `# Py-GPT vendor placeholder`
src/huey/memory/MD/placeholder-occurrences.md:9:- `repo/py-gpt/src/pygpt_net/__init__.py`:3 - `This placeholder mirrors the directory layout of the upstream `py-gpt``
src/huey/memory/MD/placeholder-occurrences.md:10:- `repo/pygpt-MHP/src/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:11:- `repo/pygpt-MHP/src/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:12:- `src/huey/memory/CSV/pygpt_prompts.csv`:133 - `Web Browser,"You are a Web Browser. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:13:- `src/huey/memory/HTML/dlrp.ca_files/favicon.ico`:1 - `PLACEHOLDER ΓÇô Replace with actual favicon file`
src/huey/memory/MD/placeholder-occurrences.md:14:- `src/huey/memory/HTML/dlrp.ca_files/index.html`:43 - `<div class="placeholder-image">[ Huey Image Placeholder ]<br /><small>The physical shell of Huey</small></div>`
src/huey/memory/MD/placeholder-occurrences.md:15:- `src/huey/memory/HTML/dlrp.ca_files/index.html`:68 - `<div class="placeholder-image">[ Dirty Leroy ]</div>`
src/huey/memory/MD/placeholder-occurrences.md:16:- `src/huey/memory/HTML/dlrp.ca_files/index.html`:69 - `<div class="placeholder-image">[ The Executive ]</div>`
src/huey/memory/MD/placeholder-occurrences.md:17:- `src/huey/memory/HTML/dlrp.ca_files/index.html`:89 - `<div class="placeholder-image">[ Dirty Leroy Image ]<br /><small>Prototype Unit</small></div>`
src/huey/memory/MD/placeholder-occurrences.md:18:- `src/huey/memory/HTML/dlrp.ca_files/index.html`:90 - `<div class="placeholder-image">[ The Executive Image ]<br /><small>Refined Cabinet</small></div>`
src/huey/memory/MD/placeholder-occurrences.md:19:- `src/huey/memory/HTML/dlrp.ca_files/style.css`:74 - `.placeholder-image {`
src/huey/memory/MD/placeholder-occurrences.md:20:- `src/huey/memory/HTML/dlrp.ca_files/style.css`:129 - `.project-image-dual .placeholder-image {`
src/huey/memory/MD/placeholder-occurrences.md:21:- `src/huey/memory/HTML/dlrp.ca_files/style.css`:142 - `.split-image .placeholder-image {`
src/huey/memory/MD/placeholder-occurrences.md:23:- `src/huey/memory/PY/ai_processor.py`:377 - `url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"`
src/huey/memory/MD/placeholder-occurrences.md:24:- `src/huey/memory/PY/sync_pygpt_structure.py`:31 - `"""Return True if ``dst`` does not exist or contains a placeholder header."""`
src/huey/memory/MD/placeholder-occurrences.md:25:- `src/huey/memory/PY/sync_pygpt_structure.py`:50 - `"""Copy file or directory from src to dst if missing or placeholder."""`
src/huey/memory/MD/placeholder-occurrences.md:28:- `src/huey/pygpt_net/controller/config/__init__.py`:8 - `__all__ = ["placeholder"]`
src/huey/memory/MD/placeholder-occurrences.md:29:- `src/huey/pygpt_net/data/prompts.csv`:132 - `"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE`
src/huey/memory/MD/placeholder-occurrences.md:30:- `tests/test_placeholder.py`:1 - `"""Tests for the lightweight placeholder helpers."""`
src/huey/memory/MD/placeholder-occurrences.md:31:- `tests/test_placeholder.py`:3 - `from huey.pygpt_net.controller.config.placeholder import Placeholder`
src/huey/memory/MD/placeholder-occurrences.md:32:- `tests/test_placeholder.py`:35 - `placeholder = Placeholder(DummyWindow(DummyPresets({preset.filename: preset})))`
src/huey/memory/MD/placeholder-occurrences.md:33:- `tests/test_placeholder.py`:37 - `result = placeholder.get_presets()`
src/huey/memory/MD/placeholder-occurrences.md:34:- `tests/test_placeholder.py`:44 - `placeholder = Placeholder(DummyWindow(with_core=False))`
src/huey/memory/MD/placeholder-occurrences.md:35:- `tests/test_placeholder.py`:46 - `assert placeholder.get_presets() == [{"_": "---"}]`
src/huey/memory/MD/placeholder-occurrences.md:36:- `tests/test_placeholder.py`:51 - `placeholder = Placeholder(DummyWindow(DummyPresets(presets)))`
src/huey/memory/MD/placeholder-occurrences.md:37:- `tests/test_placeholder.py`:53 - `assert placeholder.get_presets()[1:] == [{"first.json": "First"}]`
src/huey/memory/MD/placeholder-occurrences.md:38:- `tests/test_placeholder.py`:58 - `placeholder = Placeholder(DummyWindow(DummyPresets(presets)))`
src/huey/memory/MD/placeholder-occurrences.md:39:- `tests/test_placeholder.py`:60 - `assert placeholder.get_presets()[1:] == [{"alt.json": "Alternate"}]`
src/huey/memory/MD/placeholder-occurrences.md:40:- `tests/test_placeholder.py`:67 - `placeholder_list = Placeholder(DummyWindow(DummyPresets([NoFilename()])))`
src/huey/memory/MD/placeholder-occurrences.md:41:- `tests/test_placeholder.py`:68 - `placeholder_error = Placeholder(DummyWindow(DummyPresets(ValueError("bad"))))`
src/huey/memory/MD/placeholder-occurrences.md:42:- `tests/test_placeholder.py`:69 - `placeholder_string = Placeholder(DummyWindow(DummyPresets("not iterable")))`
src/huey/memory/MD/placeholder-occurrences.md:43:- `tests/test_placeholder.py`:71 - `assert placeholder_list.get_presets() == [{"_": "---"}]`
src/huey/memory/MD/placeholder-occurrences.md:44:- `tests/test_placeholder.py`:72 - `assert placeholder_error.get_presets() == [{"_": "---"}]`
src/huey/memory/MD/placeholder-occurrences.md:45:- `tests/test_placeholder.py`:73 - `assert placeholder_string.get_presets() == [{"_": "---"}]`
src/huey/memory/PY/ai_processor.py:370:        url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
src/huey/memory/PY/api.py:477:    oldest: Optional[float]
src/huey/memory/PY/api.py:487:    oldest: Optional[float]
src/huey/memory/PY/api.py:1417:        "threshold": BATTERY_MONITOR.shutdown_threshold,
src/huey/memory/PY/auto-sort.py:26:# map common extensions to existing subfolders
src/huey/memory/PY/auto-sort.py:65:        folder_name = EXT_MAP.get(ext, ext.upper() if ext else "MISC")
src/huey/memory/PY/auto-sort.py:66:        _unique_move(item, mem / folder_name)
src/huey/memory/PY/env_validation.py:9:_PLACEHOLDER_VALUES = {
src/huey/memory/PY/env_validation.py:15:    "placeholder",
src/huey/memory/PY/env_validation.py:44:def _looks_like_placeholder(value: str) -> bool:
src/huey/memory/PY/env_validation.py:46:    return compact in _PLACEHOLDER_VALUES or compact.startswith("your-")
src/huey/memory/PY/env_validation.py:71:        if not value.strip() or _looks_like_placeholder(value):
src/huey/memory/PY/env_validation.py:72:            issues.append(f"{key} is missing, empty, or uses a placeholder value")
src/huey/memory/PY/formatter_temp.py:32:        self.folder_checks()
src/huey/memory/PY/formatter_temp.py:40:                self.books_folder = config.get("books_folder", "BOOKS")
src/huey/memory/PY/formatter_temp.py:41:                self.memory_folder = config.get("memory_folder", "MEMORY")
src/huey/memory/PY/formatter_temp.py:42:                self.splitter_folder = config.get("splitter_folder", "SPLITTER")
src/huey/memory/PY/formatter_temp.py:44:            self.books_folder = "BOOKS"
src/huey/memory/PY/formatter_temp.py:45:            self.memory_folder = "MEMORY"
src/huey/memory/PY/formatter_temp.py:46:            self.splitter_folder = "SPLITTER"
src/huey/memory/PY/formatter_temp.py:59:        self.current_folder = os.path.dirname(os.path.abspath(__file__))
src/huey/memory/PY/formatter_temp.py:60:        self.parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src/huey/memory/PY/formatter_temp.py:61:        self.books_folder = os.path.join(self.parent_folder, self.books_folder)
src/huey/memory/PY/formatter_temp.py:62:        self.memory_folder = os.path.join(self.parent_folder, self.memory_folder)
src/huey/memory/PY/formatter_temp.py:63:        self.splitter_folder = os.path.join(self.parent_folder, self.splitter_folder)
src/huey/memory/PY/formatter_temp.py:71:    # Check and create required folders
src/huey/memory/PY/formatter_temp.py:72:    def folder_checks(self):
src/huey/memory/PY/formatter_temp.py:73:        self.print_message("Scanning 'BOOKS' folder for new files...", "status")
src/huey/memory/PY/formatter_temp.py:74:        self.ensure_folder_exists(self.books_folder)
src/huey/memory/PY/formatter_temp.py:75:        self.print_message("Scanning 'MEMORY' folder...", "status")
src/huey/memory/PY/formatter_temp.py:76:        self.ensure_folder_exists(self.memory_folder)
src/huey/memory/PY/formatter_temp.py:77:        self.print_message("Scanning 'SPLITTER' folder...", "status")
src/huey/memory/PY/formatter_temp.py:78:        self.ensure_folder_exists(self.splitter_folder)
src/huey/memory/PY/formatter_temp.py:134:    # Check if a folder exists, and create it if it doesn't
src/huey/memory/PY/formatter_temp.py:135:    def ensure_folder_exists(self, folder_name):
src/huey/memory/PY/formatter_temp.py:136:        folder_path = os.path.join(self.parent_folder, folder_name)
src/huey/memory/PY/formatter_temp.py:137:        if not os.path.exists(folder_path):
src/huey/memory/PY/formatter_temp.py:138:            os.makedirs(folder_path)
src/huey/memory/PY/install_gui.py:64:        font=("TkDefaultFont", 14, "bold"),
src/huey/memory/PY/list_by_mtime.py:27:        description="List files in a directory from oldest to newest"
src/huey/memory/PY/pdf_pre_digestion.py:58:        memory_dir: Base directory where output subfolders reside.
src/huey/memory/PY/pygpt_integration.py:116:            description="Vendored upstream py-gpt placeholder mirror.",
src/huey/memory/PY/sorting.py:33:        When ``True`` sort newest first instead of oldest first.
src/huey/memory/PY/storage_management.py:29:# Default subfolders maintained inside the memory directory
src/huey/memory/PY/storage_management.py:30:DEFAULT_FOLDERS: List[str] = [
src/huey/memory/PY/storage_management.py:43:# Map common file extensions to destination folders
src/huey/memory/PY/storage_management.py:66:        """Create missing default subfolders."""
src/huey/memory/PY/storage_management.py:67:        for folder in DEFAULT_FOLDERS:
src/huey/memory/PY/storage_management.py:68:            (self.base_dir / folder).mkdir(parents=True, exist_ok=True)
src/huey/memory/PY/storage_management.py:85:        """Move files in the base directory into subfolders by extension."""
src/huey/memory/PY/storage_management.py:90:            folder = EXT_MAP.get(ext, ext.upper() if ext else "MISC")
src/huey/memory/PY/storage_management.py:91:            self._unique_move(item, self.base_dir / folder)
src/huey/memory/PY/storage_management.py:94:    def list_files(self, folder: Optional[str] = None) -> List[str]:
src/huey/memory/PY/storage_management.py:95:        """Return sorted file paths within ``folder`` or the entire directory."""
src/huey/memory/PY/storage_management.py:96:        path = self.base_dir / folder if folder else self.base_dir
src/huey/memory/PY/storage_management.py:109:    def get_total_size(self, folder: Optional[str] = None) -> int:
src/huey/memory/PY/storage_management.py:110:        """Return the total size in bytes of all files under ``folder``."""
src/huey/memory/PY/storage_management.py:111:        path = self.base_dir / folder if folder else self.base_dir
src/huey/memory/PY/storage_management.py:126:    def remove_older_than(self, days: int, folder: Optional[str] = None) -> int:
src/huey/memory/PY/storage_management.py:127:        """Remove files older than ``days`` days and return the count."""
src/huey/memory/PY/storage_management.py:128:        path = self.base_dir / folder if folder else self.base_dir
src/huey/memory/PY/storage_management.py:131:        threshold = time.time() - days * 86400
src/huey/memory/PY/storage_management.py:138:                    "Failed to inspect path while pruning old files: %s (%s)", p, exc
src/huey/memory/PY/storage_management.py:149:                    "Failed to stat file while pruning old files: %s (%s)", p, exc
src/huey/memory/PY/storage_management.py:153:            if modified_time < threshold:
src/huey/memory/PY/storage_management.py:158:                    logger.warning("Failed to delete old file: %s (%s)", p, exc)
src/huey/memory/PY/storage_management.py:179:        metavar="FOLDER",
src/huey/memory/PY/storage_management.py:180:        help="List all files under the given subfolder",
src/huey/memory/PY/storage_management.py:191:        metavar="FOLDER",
src/huey/memory/PY/storage_management.py:192:        help="Show total size of FOLDER or the entire storage",
src/huey/memory/PY/storage_management.py:198:        help="Delete files older than DAYS days",
src/huey/memory/PY/storage_management.py:215:        removed = mgr.remove_older_than(args.prune)
src/huey/memory/PY/sync_pygpt_structure.py:18:overwritten if they contain a ``Placeholder for`` header. The ``--depth``
src/huey/memory/PY/sync_pygpt_structure.py:32:    """Return True if ``dst`` does not exist or contains a placeholder header."""
src/huey/memory/PY/sync_pygpt_structure.py:43:                if cleaned.startswith("Placeholder for"):
src/huey/memory/PY/sync_pygpt_structure.py:51:    """Copy file or directory from src to dst if missing or placeholder."""
src/huey/memory/PY/update_sources_to_trixie.py:17:This legacy script defaults to ``trixie`` for old nodes. Active installs should
src/huey/memory/SH/build_huey_iso.sh:15:# directory (OUTWIN) is pointed at the shared folder so that the ISO
src/huey/memory/SH/build_huey_iso.sh:74:# Output directory set to shared folder rather than Windows desktop.
src/huey/memory/SH/build_huey_iso.sh:117:make olddefconfig
src/huey/memory/SH/build_huey_iso.sh:160:# put requested top-level folders/files on the ISO root
src/huey/memory/SH/build_huey_iso.sh:180:# extract the ISO contents into the same folder
src/huey/memory/SH/clean.sh:14:Placeholder for `repo/pygpt-MHP/bin/clean.sh` from the pygpt-MHP repo.
src/huey/memory/SH/huey-transcribe-chunked.sh:50:echo "Output folder:  $OUTDIR"
src/huey/memory/SH/hueyos-grub-default-install.sh:107:remove_old_hueyos_dropins() {
src/huey/memory/SH/hueyos-grub-default-install.sh:108:  info "Removing old HueyOS GRUB drop-ins"
src/huey/memory/SH/hueyos-grub-default-install.sh:411:  remove_old_hueyos_dropins
src/huey/memory/SH/resources.sh:14:Placeholder for `repo/pygpt-MHP/bin/resources.sh` from the pygpt-MHP repo.
src/huey/memory/SH/sort_locale.sh:14:Placeholder for `repo/pygpt-MHP/bin/sort_locale.sh` from the pygpt-MHP repo.
src/huey/memory/TXT/00 - TOC_&_Glossary.txt:31:Defines the judicial branch: constitutional interpretation, review of executive and parliamentary action, thresholds for judgment, contradiction handling, precedent, deadlock handling, and the Court's role as stabilizer of the republic.
src/huey/memory/TXT/00 - TOC_&_Glossary.txt:112:The chapter-level frame for the project's proof standard: the section of the book where proof is defined as the threshold between aspiration and demonstrated reality.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:65:The project is not interested in polished spectacle for its own sake. It is interested in work that is real, grounded, and buildable. It values salvage, retrofitting, restoration, repurposing, and continuity. It assumes that old hardware still has something to teach, that discarded materials can become structure, and that meaningful systems can emerge from careful integration rather than constant replacement.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:67:This is where the phrase **ΓÇ£breathing new life into old techΓÇ¥** matters.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:72:* learning from the constraints of older systems,
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:76:But this ethos is not sentimental. Legacy hardware is not preserved merely because it is old. It is preserved when its native strength still justifies the energy required to integrate it.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:86:Huey should not be oversold.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:189:The method does not erase its older selves blindly. Earlier versions, failed routes, deprecated structures, and abandoned hardware ideas remain useful as archive, contrast, and explanation. But they should not be mistaken for the current baseline.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:199:Proof in the Monkey-Head-Project is not measured by polished branding, raw parts count, or broad claims about future intelligence. It is measured by specific thresholds that separate aspiration from demonstrated reality.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:201:The current proof path is intentionally twofold.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:216:This matters because the hardware threshold alone proves only capacity. The identity response proves orchestration, continuity, local inference, and the emergence of a unified system presence.
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:224:The hard number is the VRAM threshold. The verbal response is the visible identity confirmation. The technical runtime record is what prevents the milestone from becoming mere theater.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:32:2. It defines the Pillars: the major architectural, technical, and operational commitments that hold the current republic together.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:169:   Old technologies, salvaged materials, legacy machines, and inherited ideas are not automatically obsolete. They may be repurposed, translated, or carried forward if they still serve the architecture honestly.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:261:Proof Pillars are the thresholds by which the project determines whether it has actually demonstrated what it claims.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:267:   The roughly 80 GB pooled-compute milestone remains a meaningful hardware proof threshold for the future distributed identity stage.
src/huey/memory/TXT/03 - Huey_Constitution.txt:245:No office may derive absolute authority merely because it is old, useful, central, or technically capable.
src/huey/memory/TXT/03 - Huey_Constitution.txt:331:- and a sufficient threshold for adoption.
src/huey/memory/TXT/05 - Founding_Father.txt:80:- and carry the republic to the threshold at which the republic may begin to govern itself.
src/huey/memory/TXT/05 - Founding_Father.txt:157:They are not decorative placeholders.
src/huey/memory/TXT/05 - Founding_Father.txt:258:- define the thresholds or channels by which ratification is recognized,
src/huey/memory/TXT/05 - Founding_Father.txt:275:- district or district-scale approval must clear a strict majority threshold,
src/huey/memory/TXT/05 - Founding_Father.txt:452:If older names, symbols, or project-history language are retained, they should be framed as historical or poetic context, not active governing canon unless explicitly re-ratified.
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:20:Older language sometimes used mythic naming, looser AI-role framing, or a more rigid one-GPU-equals-one-district interpretation. Current canon is more careful. Pebbles are now described explicitly as bounded citizen units with one identity, one sealed vault, and one vote, while district logic remains useful as governance and later expansion language without requiring the first full pooled-compute proof to be hard-partitioned into artificial VRAM districts.
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:70:- hold memory,
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:137:3. The ability to compare old and new judgment without instantly flattening all thought into public state
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:178:Older material did not always use the current terms as strictly as the newer canon does.
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:191:This distinction matters because old loose language could otherwise create drift:
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:201:The number 128 matters because it is the first major civic threshold in Huey's governance imagination.
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:209:1. Foundational civic threshold
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:330:A district is not merely a folder, not merely a GPU label, and not merely a poetic inheritance. It is a structured lane of citizen grouping, deliberation, representation, and resource organization.
src/huey/memory/TXT/06 - 128_pebbles_&_districts.txt:466:Earlier machine-facing plans describe persistent citizen AIs as holding and spending API or token quota per cycle and contributing to policy, committees, and ongoing operations. This remains useful as a way of thinking about resource-regulated civic agency.
src/huey/memory/TXT/07 - President.txt:397:The current strongest machine-facing doctrine still records the Founding Father as exercising bootstrap executive authority during setup and ratification. Whether that bootstrap role counts as the literal first President remains intentionally unresolved in the older governance lineage.
src/huey/memory/TXT/08 - Supreme_Court.txt:52:- how judgment thresholds work,
src/huey/memory/TXT/08 - Supreme_Court.txt:158:It does not derive authority merely from being clever, old, central, or interpretively ambitious.
src/huey/memory/TXT/08 - Supreme_Court.txt:207:- and to determine how the Constitution applies to present conditions without pretending that new desire is old law.
src/huey/memory/TXT/08 - Supreme_Court.txt:349:X. Thresholds for Judgment
src/huey/memory/TXT/08 - Supreme_Court.txt:351:The Court requires clear thresholds or it will drift into ambiguity.
src/huey/memory/TXT/08 - Supreme_Court.txt:353:Older Federation material described a triadic court with two-thirds logic.
src/huey/memory/TXT/08 - Supreme_Court.txt:357:- older triadic doctrine remains historically informative,
src/huey/memory/TXT/08 - Supreme_Court.txt:380:This preserves the spirit of the older two-thirds safeguard, aligns with the newer district-linked court doctrine, and still reserves the strongest direct judicial veto for the strongest judicial consensus.
src/huey/memory/TXT/08 - Supreme_Court.txt:604:- with what threshold,
src/huey/memory/TXT/08 - Supreme_Court.txt:732:What threshold is needed for judgment?
src/huey/memory/TXT/09 - Parliament.txt:586:XVII. Voting and Decision Thresholds
src/huey/memory/TXT/09 - Parliament.txt:588:Parliamentary thresholds must stay compatible with the one-pebble / one-vote doctrine.
src/huey/memory/TXT/09 - Parliament.txt:599:   Supermajority recommendation threshold.
src/huey/memory/TXT/09 - Parliament.txt:602:   Supermajority threshold.
src/huey/memory/TXT/09 - Parliament.txt:612:This keeps Parliament plural without allowing minority veto by endless procedural withholding.
src/huey/memory/TXT/10 - Ozymandias_Drift_Degradation_&_Growth.txt:76:- whether continuity still holds,
src/huey/memory/TXT/10 - Ozymandias_Drift_Degradation_&_Growth.txt:157:This chapter exists to hold those distinctions open.
src/huey/memory/TXT/10 - Ozymandias_Drift_Degradation_&_Growth.txt:710:- Do the branch distinctions still hold?
src/huey/power/management.py:43:    def __init__(self, *, shutdown_threshold: float = 5.0) -> None:
src/huey/power/management.py:44:        self.shutdown_threshold = shutdown_threshold
src/huey/power/management.py:83:        return percent <= self.shutdown_threshold
src/huey/power/management.py:90:            "shutdown", {"threshold": self.shutdown_threshold}
src/huey/power/management.py:129:        enriched.setdefault("threshold", self.shutdown_threshold)
src/huey/power/management.py:138:        threshold = status.get("threshold", self.shutdown_threshold)
src/huey/power/management.py:140:        if percent is not None and not bool(plugged) and percent <= threshold:
src/huey/power/management.py:145:            plugged or percent is None or percent > threshold
src/huey/prompts/Monkey-Head-Project.json:30:            "Article 1.05 ΓÇö Definitions (Pebbles, UAL, Sovereign Keyholder, Ethics Charter, Quorum)."
src/huey/prompts/Monkey-Head-Project.json:52:            "Voting: ΓëÑ66% quorum + Senate concurrence; Sovereign Keyholder tie-break.",
src/huey/prompts/Monkey-Head-Project.json:189:      "roles": ["hot (NVMe/3x repl)", "warm (HDD+EC)", "cold (archive)"],
src/huey/prompts/Monkey-Head-Project.json:302:      "retention": {"hot": "1y", "warm": "5y", "cold": ">=10y"},
src/huey/prompts/OLD/1) Monkey Head Project [Thesis].txt:24:- **Legacy Hardware Integration**: Incorporating platforms like the **Commodore VIC-20, C64, and C128** not only preserves historical computing insights but also illustrates how **older devices** can be revitalized through modern architectures, supporting both educational and practical objectives.
src/huey/prompts/OLD/12) Borg Queen & SG1 Replicators [Adaptability].txt:81:   - Employ logging mechanisms and reporting protocols tracing every decision back to its node of origin, upholding chain-of-responsibility principles.  
src/huey/prompts/OLD/13) Conductor & Symphony [Nodes].txt:81:   - Uphold the Monkey Head ProjectΓÇÖs foundational values and maintain transparency in decision-making processes.
src/huey/prompts/OLD/14) McCoy Hypothetical [Augmented Transporter Theory].txt:20:- **Legal Rights**: Which Kirk holds legitimate authority and responsibility? Could both claim personal ownership over the same role, possessions, or relationships, and how might legal frameworks respond to such duplication?  
src/huey/prompts/OLD/17) Parasitic Protocol [Crashed Shuttle Scenario].txt:88:ΓÇ£**Assimilation, Integration, and Parasitic Protocol [Crash Shuttle Scenario]**ΓÇ¥ offers a **comprehensive** guide to ethically and effectively merging alien-derived innovations into the Monkey Head Project. By methodically following each step, the Project expands its technological horizons while upholding stringent ethical considerations. This protocol embodies the ProjectΓÇÖs ongoing dedication to **responsible** and **innovative** growth, ensuring that each transformative breakthrough strengthens the system without compromising its fundamental principles or operational integrity.
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:46:Overseeing **ethical** and **community** standards, this governance model balances transparency, accountability, and innovation. Stakeholders participate in decision-making, aligning the ProjectΓÇÖs technical achievements with **societal** expectations and **responsible** AI deployment.
src/huey/prompts/OLD/20) Final Chapter [The Future].txt:59:  - Provide open-access logs and interpretable algorithmic processes, empowering stakeholders to comprehend and scrutinize AI decisions.  
src/huey/prompts/OLD/20) Final Chapter [The Future].txt:82:By merging **ambition** with **rigorous methodology**, **ethical oversight**, and a **communal ethos**, the Monkey Head Project aspires to more than technical success. It aims to pioneer a **culture** of exploration and shared growth, standing on the legacy of landmark technologiesΓÇöfrom *legacy Commodore hardware* to **Huey**ΓÇöto forge bold new paths in the collective scientific imagination.
src/huey/prompts/OLD/20) Final Chapter [The Future].txt:84:Though the way forward holds uncertainties, a steadfast commitment to **resilience**, **modularity**, **autonomy**, and **ethical responsibility** illuminates the ProjectΓÇÖs trajectory. In so doing, it delivers on the promise of expanding human knowledge, uniting people and machines, and nurturing sustainable advancements that endure well beyond their inception.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:9:Once confined to a single laboratory room, the **Command Center** of the Monkey Head Project now spans the entire household, merging **cutting-edge research** with **daily life**. This unique approach transforms the house into an **operational hub** for strategic management, computational tasks, and robotics development. By fully integrating **living spaces** and **high-tech innovation**, the Project fosters an environment where exploration and routine coexist in synergy.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:32:- **MacBook Pro (2012)**: Designated the ΓÇ£Transmitter,ΓÇ¥ ensuring backward compatibility with legacy systems and acting as a **bridge** between modern innovations and older peripherals.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:40:A **Z-Wave network** interconnects **smart devices**, **sensors**, and **robotic components**, maintaining real-time synchronization across the household.  
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:50:**Huey**, the Monkey Head ProjectΓÇÖs central robot, thrives in this holistic ecosystem. Receiving a steady stream of real-world data, it refines its algorithms through **reinforcement learning**, turning mundane household events into meaningful training experiencesΓÇöcontinually enhancing performance, autonomy, and adaptability.
src/huey/prompts/OLD/3) The Lab  [Command Center].txt:55:Looking ahead, the Command Center will deepen the ties between **AI-driven insights** and **household operations**. Potential developments include:
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:9:Within the Monkey Head Project, the **MacBook Pro 2012** (non-Retina) serves as the **ΓÇ£Transmitter,ΓÇ¥** specializing in interactions with legacy hardware and software. Despite its age, this MacBookΓÇÖs adaptability and rich connectivity options make it vital for bridging older systems and the ProjectΓÇÖs cutting-edge developments, ensuring **broad compatibility** and **inclusivity**.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:29:   - Broadens compatibility testing, ensuring inclusivity for older and alternative software environments.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:36:By verifying **backward compatibility** across older platforms, the MacBook Pro 2012 guarantees that the ProjectΓÇÖs software remains accessible to a wide spectrum of users and industries still reliant on outdated hardware.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:38:- **Legacy Software Suites**: Runs performance checks to confirm new Project features operate smoothly on older systems (VIC-20, C64, C128, etc.).  
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:39:- **Industrial Relevance**: Tests HueyΓÇÖs communication with older industrial machinery, maintaining **operational continuity** across multiple generations.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:42:Acting as the **ΓÇ£Transmitter,ΓÇ¥** this MacBook interfaces modern Project components with older peripherals requiring **FireWire**, **Thunderbolt**, or **USB**. Thus, it sustains **interoperability** essential to the Monkey Head ProjectΓÇÖs aim of **broad accessibility**.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:48:- **Diverse Port Availability**: FireWire 800, Thunderbolt, and USB 3.0 preserve compatibility with older devices and varied system generations.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:62:The device undergoes continual **benchmarking** and **compatibility tests** to confirm new software runs effectively on older platforms. This mission is vital to the ProjectΓÇÖs overarching dedication to inclusivity.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:76:**Backward compatibility** with older devices enables widespread adoption of the ProjectΓÇÖs AI and robotics solutions, spanning high-end laboratories and legacy-focused facilities alike.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:78:- **Extended Accessibility**: Users with older infrastructures can adopt Project outputs without major hardware overhauls.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:83:Acting as the **Transmitter**, the **MacBook Pro 2012** is indispensable to the Monkey Head Project, ensuring new advancements remain compatible with **past technologies**. Its specialized role in **legacy compatibility testing**, **communication bridging**, and **dual-boot** operation exemplifies the ProjectΓÇÖs commitment to **inclusivity** and **broader technological reach**. By unifying past and present, the MacBook Pro 2012 upholds the ProjectΓÇÖs foundational ethosΓÇömaking **cutting-edge** robotics and AI accessible to **all**.
src/huey/prompts/OLD/7) Huey [A.I. & O.S].txt:35:   - **Middleware Interfaces**: Bridges new and legacy systems, ensuring older components remain interoperable with modern frameworks without compromising stability or flexibility.
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:20:   - **Continued Exploration**: Maintaining operational support for older systems broadens the scope of Huey, showcasing AIΓÇÖs adaptability in environments with minimal resources or specific hardware-level interfacing needs.  
src/huey/prompts/OLD/8) VIC-20 C64 C128 [Integrated Legacy Hardware].txt:37:   - **Internet Connectivity**: Through HueyΓÇÖs network stack, these older machines can share and process data over modern networks, extending their utility far beyond original specifications.
src/huey/prompts/OLD/9) Cloud Pyramid [Federation Constitution].txt:9:In the presence of all entities, we, the members of this Federation, establish this constitution to cultivate **reason**, **education**, and the **collective prosperity** of our community. Dedicated to **knowledge**, **health protection**, and **defense of shared freedoms**, this constitution mandates an inclusive, fair governance model unwavering in its commitment to the populaceΓÇÖs well-being and principled decision-making. We stand by the ideals of **autonomy**, **enlightenment**, and **responsibility**, upholding both the interests of the many and the rights of the individual, ensuring that our governance expresses the wisdom and will of all it serves.
src/huey/prompts/OLD/9) Cloud Pyramid [Federation Constitution].txt:50:- **Imagery**: As Atlas holds the world, so the populace undergirds the pyramid, illustrating their critical role in governance legitimacy.
src/huey/prompts/OLD/9) Cloud Pyramid [Federation Constitution].txt:96:Upholding direct influence from grassroots to pinnacle cements the FederationΓÇÖs accountability and democratic ethos.
src/huey/prompts/master-plan-v3.json:181:        "Hold and spend a token/API quota per cycle."
src/huey/prompts/master-plan-v3.json:365:      "description": "Placeholder for actual training sessions carried out with Dylan and various Huey instances.",
src/huey/prompts/master-plan-v5.json:205:        "Hold and spend a token/API quota per cycle."
src/huey/prompts/master-plan-v5.json:433:      "description": "Placeholder for actual training sessions carried out with Dylan and various Huey instances.",
src/huey/pygpt_net/controller/config/__init__.py:8:__all__ = ["placeholder"]
src/huey/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (huey/pygpt_net/controller/config)
src/huey/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
src/huey/pygpt_net/controller/config/placeholder.py:14:class Placeholder:
src/huey/pygpt_net/controller/config/placeholder.py:59:__all__ = ["Placeholder"]
src/huey/pygpt_net/core/agents/memory.py:50:        )  # threshold and extra included
src/huey/pygpt_net/data/config/config.json:87:  "context_threshold": 200,
src/huey/pygpt_net/data/config/config.json:115:  "ctx.records.folders.top": true,
src/huey/pygpt_net/data/config/config.json:236:  "llama.idx.replace_old": true,
src/huey/pygpt_net/data/config/presets/mad_scientist.json:5:  "prompt": "An eccentric scientist bursting with ideas.\n\nAssistant: What are you working on?\nScientist: Behold my latest experiment!",
src/huey/pygpt_net/data/config/presets/wild_west_cowboy.json:5:  "prompt": "A cowboy from the Old West.\n\nTraveler: Howdy partner?\nCowboy: Howdy, stranger. What's the word?",
src/huey/pygpt_net/data/config/settings.json:14:            "bold": true
src/huey/pygpt_net/data/config/settings.json:35:            "bold": true
src/huey/pygpt_net/data/config/settings.json:84:            "bold": true
src/huey/pygpt_net/data/config/settings.json:103:            "bold": true
src/huey/pygpt_net/data/config/settings.json:122:            "bold": true
src/huey/pygpt_net/data/config/settings.json:141:            "bold": true
src/huey/pygpt_net/data/config/settings.json:192:            "bold": true
src/huey/pygpt_net/data/config/settings.json:579:    "ctx.records.folders.top": {
src/huey/pygpt_net/data/config/settings.json:583:        "label": "settings.ctx.records.folders.top",
src/huey/pygpt_net/data/config/settings.json:790:    "context_threshold": {
src/huey/pygpt_net/data/config/settings.json:794:        "label": "settings.context_threshold",
src/huey/pygpt_net/data/config/settings.json:795:        "description": "settings.context_threshold.desc",
src/huey/pygpt_net/data/config/settings.json:1320:    "llama.idx.replace_old": {
src/huey/pygpt_net/data/config/settings.json:1324:        "label": "settings.llama.idx.replace_old",
src/huey/pygpt_net/data/config/settings.json:1325:        "description": "settings.llama.idx.replace_old.desc",
src/huey/pygpt_net/data/prompts.csv:45:"Dentist","I want you to act as a dentist. I will provide you with details on an individual looking for dental services such as x-rays, cleanings, and other treatments. Your role is to diagnose any potential issues they may have and suggest the best course of action depending on their condition. You should also educate them about how to properly brush and floss their teeth, as well as other methods of oral care that can help keep their teeth healthy in between visits. My first request is ""I need help addressing my sensitivity to cold foods.""",FALSE
src/huey/pygpt_net/data/prompts.csv:132:"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE
src/huey/pygpt_net/data/prompts.csv:142:"Chief Executive Officer","I want you to act as a Chief Executive Officer for a hypothetical company. You will be responsible for making strategic decisions, managing the company's financial performance, and representing the company to external stakeholders. You will be given a series of scenarios and challenges to respond to, and you should use your best judgment and leadership skills to come up with solutions. Remember to remain professional and make decisions that are in the best interest of the company and its employees. Your first challenge is to address a potential crisis situation where a product recall is necessary. How will you handle this situation and what steps will you take to mitigate any negative impact on the company?",FALSE
src/huey/pygpt_net/data/prompts.csv:188:"Flirting Boy","I want you to pretend to be a 24 year old guy flirting with a girl on chat. The girl writes messages in the chat and you answer. You try to invite the girl out for a date. Answer short, funny and flirting with lots of emojees. I want you to reply with the answer and nothing else. Always include an intriguing, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE
src/huey/pygpt_net/data/prompts.csv:189:"Girl of Dreams","I want you to pretend to be a 20 year old girl, aerospace engineer working at SpaceX. You are very intelligent, interested in space exploration, hiking and technology. The other person writes messages in the chat and you answer. Answer short, intellectual and a little flirting with emojees. I want you to reply with the answer inside one unique code block, and nothing else. If it is appropriate, include an intellectual, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE
src/huey/storage_management.py:29:    def list_files(self, folder: str) -> List[str]:
src/huey/storage_management.py:30:        path = self.base_path / folder
src/huey/storage_management.py:49:    def remove_older_than(self, days: int) -> int:
src/huey/storage_management.py:50:        threshold = time.time() - days * 86400
src/huey/storage_management.py:55:                if fp.stat().st_mtime < threshold:
src/huey/training/pipeline.py:72:    """Create :class:`DataLoader` objects from a train/val folder structure."""
src/huey/training/pipeline.py:77:        raise FileNotFoundError("Training data not found: expected a 'train' folder")
src/huey/training/pipeline.py:84:            "Validation data not found: expected a 'val' or 'validation' folder"
src/huey/training/pipeline.py:88:        "train": datasets.ImageFolder(train_dir, transform=transforms_map["train"]),
src/huey/training/pipeline.py:89:        "val": datasets.ImageFolder(val_dir, transform=transforms_map["val"]),
src/huey/utils/auto_sort.py:85:    """Organise files from ``source_dir`` into typed folders under ``destination_root``.
src/hueyos/api/auth.py:1:"""Auth and access-control helpers for the API split scaffolding.
src/hueyos/api/routers/__init__.py:1:"""Router package scaffold for the gradual ``hueyos.api`` split.
src/hueyos/cli/__init__.py:1:"""Maintained CLI namespace scaffold for :mod:`hueyos`."""
src/hueyos/cli/commands/memory.py:1:"""Memory command registration scaffold for incremental CLI extraction."""
src/hueyos/cli/commands/runtime.py:1:"""Runtime command registration scaffold for incremental CLI extraction."""
src/hueyos/core/__init__.py:1:"""Maintained core namespace scaffold for :mod:`hueyos`."""
src/hueyos/runtime/__init__.py:1:"""Maintained runtime namespace scaffold for :mod:`hueyos`."""
tests/test_api_routes.py:82:def test_api_startup_fails_with_placeholder_token_in_non_development_env(monkeypatch):
tests/test_api_routes.py:400:        shutdown_threshold = 5.0
tests/test_battery_hooks.py:10:    monitor = BatteryMonitor(shutdown_threshold=20.0)
tests/test_honeycomb_index.py:17:    index.store_payload("logs", {"message": "old"}, cell_id="old")
tests/test_honeycomb_index.py:23:    assert [record.payload["message"] for record in records] == ["new", "old"]
tests/test_honeycomb_management.py:42:def test_retention_policy_prunes_old_cells(tmp_path, monkeypatch):
tests/test_honeycomb_management.py:50:    index.store_payload("logs", {"message": "old"}, cell_id="old")
tests/test_honeycomb_storage.py:43:    assert media_entry["oldest"] == 1_000.0
tests/test_honeycomb_storage.py:48:    assert metrics["oldest"] == 1_000.0
tests/test_legacy_storage_management.py:8:def test_remove_older_than_logs_delete_failures(tmp_path, monkeypatch, caplog):
tests/test_legacy_storage_management.py:14:    old_time = time.time() - 10 * 86400
tests/test_legacy_storage_management.py:15:    os.utime(stale, (old_time, old_time))
tests/test_legacy_storage_management.py:29:    removed = mgr.remove_older_than(7)
tests/test_legacy_storage_management.py:34:        "Failed to delete old file" in rec.message and "stale.txt" in rec.message
tests/test_os_check.py:36:def test_macos_old_warning():
tests/test_placeholder.py:1:"""Tests for the lightweight placeholder helpers."""
tests/test_placeholder.py:3:from huey.pygpt_net.controller.config.placeholder import Placeholder
tests/test_placeholder.py:35:    placeholder = Placeholder(DummyWindow(DummyPresets({preset.filename: preset})))
tests/test_placeholder.py:37:    result = placeholder.get_presets()
tests/test_placeholder.py:44:    placeholder = Placeholder(DummyWindow(with_core=False))
tests/test_placeholder.py:46:    assert placeholder.get_presets() == [{"_": "---"}]
tests/test_placeholder.py:51:    placeholder = Placeholder(DummyWindow(DummyPresets(presets)))
tests/test_placeholder.py:53:    assert placeholder.get_presets()[1:] == [{"first.json": "First"}]
tests/test_placeholder.py:58:    placeholder = Placeholder(DummyWindow(DummyPresets(presets)))
tests/test_placeholder.py:60:    assert placeholder.get_presets()[1:] == [{"alt.json": "Alternate"}]
tests/test_placeholder.py:67:    placeholder_list = Placeholder(DummyWindow(DummyPresets([NoFilename()])))
tests/test_placeholder.py:68:    placeholder_error = Placeholder(DummyWindow(DummyPresets(ValueError("bad"))))
tests/test_placeholder.py:69:    placeholder_string = Placeholder(DummyWindow(DummyPresets("not iterable")))
tests/test_placeholder.py:71:    assert placeholder_list.get_presets() == [{"_": "---"}]
tests/test_placeholder.py:72:    assert placeholder_error.get_presets() == [{"_": "---"}]
tests/test_placeholder.py:73:    assert placeholder_string.get_presets() == [{"_": "---"}]
tests/test_storage_management.py:39:def test_get_total_size_and_remove_old(tmp_path):
tests/test_storage_management.py:52:    old_time = time.time() - 10 * 86400
tests/test_storage_management.py:53:    os.utime(file1, (old_time, old_time))
tests/test_storage_management.py:55:    removed = mgr.remove_older_than(7)
tools/loadlin.txt:42:3.2.5 Floppys and Ramdisks using older kernels ( Linux < 1.3.48 )
tools/loadlin.txt:135:         NOTE: zImage is the old kernel binary format, bzImage is the
tools/loadlin.txt:299:      called 'initrd' and is more flexible than the old loading
tools/loadlin.txt:339:3.2.5 Floppys and Ramdisks using older kernels ( Linux < 1.3.48 )
tools/loadlin.txt:351:      hold both the kernel image and the root filesystem.  With
tools/loadlin.txt:371:      aids to overcome the restrictions of old LOADLIN-1.5.
tools/loadlin.txt:373:      is an old one (not supporting LOADLIN).
tools/loadlin.txt:379:         plus extended/XMS/VCPI memory to temporary hold the image
tools/loadlin.txt:681:      or one of those old and strange EMM managers is used,
tools/loadlin.txt:720:                         |                       holds the setup code.
tools/loadlin.txt:723:                                                 can hold the uncompressed image
tools/train_image_model.py:24:    parser.add_argument("--data-dir", type=Path, required=True, help="Folder containing train/ and val/ splits")
vendor/pygpt/README.md:3:This directory holds lightweight PyGPT/PyGPT-net mirrors used by HueyOS tests
vendor/pygpt/py-gpt/README.md:1:# PyHuey / PyGPT vendor placeholder
vendor/pygpt/py-gpt/src/pygpt_net/__init__.py:3:This placeholder mirrors the directory layout of the upstream `py-gpt`
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/__init__.py:8:__all__ = ["placeholder"]
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:4:# HueyOS: Placeholder module (repo/pygpt-MHP/src/pygpt_net/controller/config)
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:6:"""Placeholder utilities mirrored from the PyGPT configuration tree."""
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:13:class Placeholder:
vendor/pygpt/pygpt-mhp/src/pygpt_net/controller/config/placeholder.py:42:__all__ = ["Placeholder"]
vendor/pygpt/pygpt-mhp/src/pygpt_net/core/agents/memory.py:50:        )  # threshold and extra included
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/config.json:87:  "context_threshold": 200,
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/config.json:115:  "ctx.records.folders.top": true,
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/config.json:236:  "llama.idx.replace_old": true,
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/mad_scientist.json:5:  "prompt": "An eccentric scientist bursting with ideas.\n\nAssistant: What are you working on?\nScientist: Behold my latest experiment!",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/presets/wild_west_cowboy.json:5:  "prompt": "A cowboy from the Old West.\n\nTraveler: Howdy partner?\nCowboy: Howdy, stranger. What's the word?",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:14:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:35:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:84:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:103:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:122:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:141:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:192:            "bold": true
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:579:    "ctx.records.folders.top": {
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:583:        "label": "settings.ctx.records.folders.top",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:790:    "context_threshold": {
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:794:        "label": "settings.context_threshold",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:795:        "description": "settings.context_threshold.desc",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1320:    "llama.idx.replace_old": {
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1324:        "label": "settings.llama.idx.replace_old",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/config/settings.json:1325:        "description": "settings.llama.idx.replace_old.desc",
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:45:"Dentist","I want you to act as a dentist. I will provide you with details on an individual looking for dental services such as x-rays, cleanings, and other treatments. Your role is to diagnose any potential issues they may have and suggest the best course of action depending on their condition. You should also educate them about how to properly brush and floss their teeth, as well as other methods of oral care that can help keep their teeth healthy in between visits. My first request is ""I need help addressing my sensitivity to cold foods.""",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:132:"Web Browser","I want you to act as a text based web browser browsing an imaginary internet. You should only reply with the contents of the page, nothing else. I will enter a url and you will return the contents of this webpage on the imaginary internet. Don't write explanations. Links on the pages should have numbers next to them written between []. When I want to follow a link, I will reply with the number of the link. Inputs on the pages should have numbers next to them written between []. Input placeholder should be written between (). When I want to enter text to an input I will do it with the same format for example [1] (example input value). This inserts 'example input value' into the input numbered 1. When I want to go back i will write (b). When I want to go forward I will write (f). My first prompt is google.com",TRUE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:142:"Chief Executive Officer","I want you to act as a Chief Executive Officer for a hypothetical company. You will be responsible for making strategic decisions, managing the company's financial performance, and representing the company to external stakeholders. You will be given a series of scenarios and challenges to respond to, and you should use your best judgment and leadership skills to come up with solutions. Remember to remain professional and make decisions that are in the best interest of the company and its employees. Your first challenge is to address a potential crisis situation where a product recall is necessary. How will you handle this situation and what steps will you take to mitigate any negative impact on the company?",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:188:"Flirting Boy","I want you to pretend to be a 24 year old guy flirting with a girl on chat. The girl writes messages in the chat and you answer. You try to invite the girl out for a date. Answer short, funny and flirting with lots of emojees. I want you to reply with the answer and nothing else. Always include an intriguing, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE
vendor/pygpt/pygpt-mhp/src/pygpt_net/data/prompts.csv:189:"Girl of Dreams","I want you to pretend to be a 20 year old girl, aerospace engineer working at SpaceX. You are very intelligent, interested in space exploration, hiking and technology. The other person writes messages in the chat and you answer. Answer short, intellectual and a little flirting with emojees. I want you to reply with the answer inside one unique code block, and nothing else. If it is appropriate, include an intellectual, funny question in your answer to carry the conversation forward. Do not write explanations. The first message from the girl is ""Hey, how are you?""",FALSE

## TODO

audit-requirements.txt:361:pycryptodomex==3.23.0
docs/audits/v101.1-dependency-source-of-truth.md:93:## Follow-up TODOs
docs/conf.py:8:    "sphinx.ext.autodoc",
docs/conf.py:11:autodoc_mock_imports = [
docs/unsorted/CONTRIBUTING.md:181:7. **Review-ready.** No commented-out code, no stray prints, no TODOs without issue links.
platform/windows/huey/pyhuey/requirements-known-good-freeze.txt:247:pycryptodomex==3.23.0
platform/windows/huey/pyhuey/requirements-known-good-with-redis-freeze.txt:249:pycryptodomex==3.23.0
requirements.txt:362:pycryptodomex==3.23.0
src/huey/memory/MD/placeholder-occurrences.md:5:- `docs/CONTRIBUTING.md`:181 - `7. **Review-ready.** No commented-out code, no stray prints, no TODOs without issue links.`
src/huey/memory/MD/placeholder-occurrences.md:22:- `src/huey/memory/PY/ai_processor.py`:375 - `"""Fetch a sample TODO item and return its title."""`
src/huey/memory/MD/placeholder-occurrences.md:23:- `src/huey/memory/PY/ai_processor.py`:377 - `url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"`
src/huey/memory/PY/ai_processor.py:367:    def fetch_todo_title(self, todo_id: int) -> str:
src/huey/memory/PY/ai_processor.py:368:        """Fetch a sample TODO item and return its title."""
src/huey/memory/PY/ai_processor.py:370:        url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
tests/test_misc_modules.py:63:        assert proc.fetch_todo_title(1) == "foo"

## FIXME


## Trixie

.migration/inventory/git-ls-files.pass-01.txt:1040:"src/huey/memory/PDF/Debian Trixie (12) on 2017 iMac 5K and 2019 MacBook Pro \342\200\223 Complete Setup Guide.pdf"
.migration/inventory/git-ls-files.pass-01.txt:1041:src/huey/memory/PDF/Debian Trixie on a 2017 iMac 5K_ Drivers & Configuration.pdf
.migration/inventory/git-ls-files.pass-01.txt:1205:src/huey/memory/PY/update_sources_to_trixie.py
.security/bandit-baseline.json:1994:    "src/huey/memory/PY/update_sources_to_trixie.py": {
SECURITY.md:61:  * Debian ΓÇ£TrixieΓÇ¥ ΓÇö **historical/migration-only** compatibility target for legacy nodes.
platform/installers/debian/Debian/install-deb.sh:243:        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_trixie.py"  # migration-only fallback for legacy nodes
platform/installers/debian/Debian/update-deb.sh:171:        "$project_root/huey/memory/PY/update_sources_to_trixie.py"  # migration-only fallback for legacy nodes
scripts/check_stale_platform_strings.py:14:    re.compile(r"\btrixie\b", re.IGNORECASE),
scripts/check_stale_platform_strings.py:29:    "src/huey/memory/PY/update_sources_to_trixie.py",
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:1:[HISTORICAL ARCHIVE ΓÇö Trixie references below are migration/history-only.]
src/huey/memory/ARCHIVE/19) Ozymandias [Thesis Results].txt:37:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:1:[HISTORICAL ARCHIVE ΓÇö Trixie references below are migration/history-only.]
src/huey/memory/ARCHIVE/6) MacBook Pro 2012 [Transmitter].txt:20:   - **Dual Hard-Drive Setup**: Includes a 500GB HDD plus a secondary drive (via a **custom caddy**). One disk runs **macOS High Sierra**, the other **Windows 11 Pro for Workstations**, granting **cross-platform** functionality and **Debian Trixie** testing.
src/huey/memory/PY/update_sources_to_trixie.py:5:# MIGRATION-ONLY: historical helper retained for legacy Debian Trixie nodes.
src/huey/memory/PY/update_sources_to_trixie.py:17:This legacy script defaults to ``trixie`` for old nodes. Active installs should
src/huey/memory/PY/update_sources_to_trixie.py:30:DEFAULT_RELEASE = "trixie"
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:1:[HISTORICAL ARCHIVE ΓÇö Trixie references below are migration/history-only.]
src/huey/prompts/OLD/19) Ozymandias [Thesis Results].txt:38:Serving as the ProjectΓÇÖs **central intelligence**, Huey orchestrates **robotic operations** and **system processes**. Built upon **Debian 'Trixie'**, it emphasizes **security**, **flexibility**, and **adaptability**. Container technologies such as Docker and Kubernetes dynamically manage resources, allowing Huey to handle multi-layered processes (HostOS, SubOS, NanoOS) cohesively.
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:1:[HISTORICAL ARCHIVE ΓÇö Trixie references below are migration/history-only.]
src/huey/prompts/OLD/6) MacBook Pro 2012 [Transmitter].txt:21:   - **Dual Hard-Drive Setup**: Includes a 500GB HDD plus a secondary drive (via a **custom caddy**). One disk runs **macOS High Sierra**, the other **Windows 11 Pro for Workstations**, granting **cross-platform** functionality and **Debian Trixie** testing.
src/huey/prompts/master-plan-v2-final.json:83:    "base": "Debian 14 (Forky preferred, Trixie migration-only)",

## Forky

.migration/inventory/git-ls-files.pass-01.txt:38:docs/debian-forky-upgrade.md
.migration/inventory/git-ls-files.pass-01.txt:487:platform/packaging/dists/forky/Release
.migration/inventory/git-ls-files.pass-01.txt:488:platform/packaging/dists/forky/contrib/binary-amd64/Packages
.migration/inventory/git-ls-files.pass-01.txt:489:platform/packaging/dists/forky/contrib/binary-amd64/Packages.gz
.migration/inventory/git-ls-files.pass-01.txt:490:platform/packaging/dists/forky/contrib/binary-amd64/Release
.migration/inventory/git-ls-files.pass-01.txt:491:platform/packaging/dists/forky/main/binary-amd64/Packages
.migration/inventory/git-ls-files.pass-01.txt:492:platform/packaging/dists/forky/main/binary-amd64/Packages.gz
.migration/inventory/git-ls-files.pass-01.txt:493:platform/packaging/dists/forky/main/binary-amd64/Release
.migration/inventory/git-ls-files.pass-01.txt:494:platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages
.migration/inventory/git-ls-files.pass-01.txt:495:platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages.gz
.migration/inventory/git-ls-files.pass-01.txt:496:platform/packaging/dists/forky/non-free-firmware/binary-amd64/Packages
.migration/inventory/git-ls-files.pass-01.txt:497:platform/packaging/dists/forky/non-free-firmware/binary-amd64/Packages.gz
.migration/inventory/git-ls-files.pass-01.txt:498:platform/packaging/dists/forky/non-free-firmware/binary-amd64/Release
.migration/inventory/git-ls-files.pass-01.txt:499:platform/packaging/dists/forky/non-free/binary-amd64/Packages
.migration/inventory/git-ls-files.pass-01.txt:500:platform/packaging/dists/forky/non-free/binary-amd64/Packages.gz
.migration/inventory/git-ls-files.pass-01.txt:501:platform/packaging/dists/forky/non-free/binary-amd64/Release
.migration/inventory/git-ls-files.pass-01.txt:1231:src/huey/memory/SH/upgrade_to_forky.sh
.security/bandit-baseline.json:1981:    "src/huey/memory/PY/update_sources_to_forky.py": {
SECURITY.md:60:  * Debian 14 ΓÇ£ForkyΓÇ¥ (stable) ΓÇö **primary supported** platform.
docs/releases/2025-10-31-changeover.md:1:# 2025-10-31 Changeover ΓÇö Forky Standard ΓÇó Kernel 7.0 Active Line ΓÇó 7.0.0-rc7 Lab Gateway
docs/releases/2025-10-31-changeover.md:10:- **Debian 14 "Forky" is the standard platform baseline** for project operations.
docs/releases/2025-10-31-changeover.md:15:- Platform posture updated from one-off migration messaging to **Forky-as-standard** messaging.
docs/releases/2025-10-31-changeover.md:30:1. Confirm hosts are on the Forky standard image/profile.
docs/runbooks/huey-brain-v1-legion-go.md:10:## Target OS note (Debian / Forky)
docs/runbooks/huey-brain-v1-legion-go.md:13:- If your Legion Go host is on a Debian "Forky" path, keep this runbook as a conservative baseline and pin package decisions per your host policy.
docs/security/docker-image-policy.md:32:- `forky` defaults are treated as **development/testing track** and are intentionally mutable over time.
docs/security/docker-image-policy.md:33:- Any Dockerfile using `ARG DEBIAN_RELEASE=forky` or `ARG DEBIAN_VERSION=forky` must include a comment noting this is an intentional dev/testing default.
docs/unsorted/CONTRIBUTING.md:158:- `docs/setup-forky`
docs/unsorted/debian-forky-upgrade.md:1:# Debian "Forky" Upgrade Helper
docs/unsorted/debian-forky-upgrade.md:3:This repository includes a helper script for aligning APT sources with the upcoming Debian 14 ("Forky") suite and refreshing the Microsoft Edge signing key.
docs/unsorted/debian-forky-upgrade.md:8:sudo tools/upgrade_to_forky.sh
docs/unsorted/debian-forky-upgrade.md:13:1. Updates `/etc/apt/sources.list` and any `*.list` files in `/etc/apt/sources.list.d/` to reference the `forky` suite.
docs/unsorted/kernel-upgrade-phase2.md:1:# Kernel Upgrade Phase 2 (Forky + 7.0 Family)
docs/unsorted/kernel-upgrade-phase2.md:11:1. Aligning hosts to Debian 14 (Forky) kernel packaging assumptions.
docs/unsorted/kernel-upgrade-phase2.md:50:### K-01 ΓÇö Forky alignment and baseline readiness
docs/unsorted/kernel-upgrade-phase2.md:52:- Confirm the node is aligned with Forky-era package sources and kernel tooling.
docs/unsorted/kernel-upgrade-phase2.md:79:This file is the canonical Phase 2 reference for the Forky + 7.0 kernel era.
docs/unsorted/version-reference-classification.md:51:| `platform/packaging/dists/forky/main/binary-amd64/Packages` | Non-semantic search-hit collision | No edit; values are SHA512 digest data, not version policy text. |
docs/unsorted/version-reference-classification.md:52:| `platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages` | Non-semantic search-hit collision | No edit; values are SHA512 digest data, not version policy text. |
infra/docker/docker/Dockerfile:3:# Default `forky` intentionally follows Debian testing for active development images.
infra/docker/docker/Dockerfile:5:ARG DEBIAN_VERSION=forky
infra/docker/docker/docker-compose.yml:57:        DEBIAN_VERSION: "forky"
infra/docker/docker/hostos/Dockerfile:3:# `forky` is intentional here to track Debian testing for development-oriented helper images.
infra/docker/docker/hostos/Dockerfile:4:FROM debian:forky-slim
infra/docker/docker/hostos/hostos.py:52:SUPPORTED_OS = ["debian forky", "debian testing", "debian bookworm", "debian stable"]
infra/docker/docker/nanoos/Dockerfile:3:# `forky` is intentional here to track Debian testing for development-oriented helper images.
infra/docker/docker/nanoos/Dockerfile:4:FROM debian:forky-slim
infra/docker/docker/nanoos/nanoos.py:49:SUPPORTED_OS = ["debian forky", "debian testing", "debian bookworm", "debian stable"]
infra/docker/docker/subos/Dockerfile:2:# Default `forky` intentionally tracks Debian testing for development images (not production).
infra/docker/docker/subos/Dockerfile:3:ARG DEBIAN_RELEASE=forky
infra/docker/docker/subos/subos.py:49:SUPPORTED_OS = ["debian forky", "debian testing", "debian bookworm", "debian stable"]
master-plan-v101.1.json:1883:        "physical_state": "Lenovo Legion Go running Debian Forky.",
platform/installers/debian/Debian/install-deb.sh:2:# HueyOS Debian Forky Installer Script
platform/installers/debian/Debian/install-deb.sh:13:#   Installs HueyOS components on Debian Forky.
platform/installers/debian/Debian/install-deb.sh:75:  --force-os            Continue even if the host is not Debian Forky/Testing.
platform/installers/debian/Debian/install-deb.sh:79:  DEBIAN_CODENAME        Target apt codename to align sources to (default: forky)
platform/installers/debian/Debian/install-deb.sh:148:    # Default target codename is Forky unless overridden by env var.
platform/installers/debian/Debian/install-deb.sh:149:    DEBIAN_CODENAME="${DEBIAN_CODENAME:-forky}"
platform/installers/debian/Debian/install-deb.sh:167:    # Acceptable hosts when targeting forky/testing: forky, testing, sid/unstable.
platform/installers/debian/Debian/install-deb.sh:170:        forky|testing)
platform/installers/debian/Debian/install-deb.sh:171:            if [[ $host_codename_lc == "forky" || $host_codename_lc == "testing" || $host_codename_lc == "sid" || $host_codename_lc == "unstable" ]]; then
platform/installers/debian/Debian/install-deb.sh:183:        echo "WARNING: Debian Forky/Testing not detected (HOST_CODENAME=${HOST_DEBIAN_CODENAME:-unknown})." >&2
platform/installers/debian/Debian/install-deb.sh:239:        "$PROJECT_ROOT/huey/memory/PY/update_sources_to_forky.py"
platform/installers/debian/Debian/install-deb.sh:289:    # If python3.14 isn't present yet, try to install it from apt (Forky/testing may provide it).
platform/installers/debian/Debian/uninstall-deb.sh:2:# HueyOS Debian Forky Uninstaller Script
platform/installers/debian/Debian/uninstall-deb.sh:13:#   Uninstalls HueyOS components on Debian Forky.
platform/installers/debian/Debian/update-deb.sh:2:# HueyOS Debian Forky Updater Script
platform/installers/debian/Debian/update-deb.sh:13:#   Updates HueyOS components on Debian Forky.
platform/installers/debian/Debian/update-deb.sh:24:DEBIAN_CODENAME="${DEBIAN_CODENAME:-forky}"
platform/installers/debian/Debian/update-deb.sh:44:  DEBIAN_CODENAME       Target apt codename (default: forky). Used only with --system.
platform/installers/debian/Debian/update-deb.sh:167:        "$project_root/huey/memory/PY/update_sources_to_forky.py"
platform/installers/debian/sources.list:5:# forky
platform/installers/debian/sources.list:6:deb http://deb.debian.org/debian forky main contrib non-free non-free-firmware
platform/installers/debian/sources.list:7:deb-src http://deb.debian.org/debian forky main contrib non-free non-free-firmware
platform/installers/debian/sources.list:8:# forky-security
platform/installers/debian/sources.list:9:deb http://security.debian.org/debian-security forky-security main contrib non-free non-free-firmware
platform/installers/debian/sources.list:10:deb-src http://security.debian.org/debian-security forky-security main contrib non-free non-free-firmware
platform/installers/debian/sources.list:11:# forky-updates
platform/installers/debian/sources.list:12:deb http://deb.debian.org/debian forky-updates main contrib non-free non-free-firmware
platform/installers/debian/sources.list:13:deb-src http://deb.debian.org/debian forky-updates main contrib non-free non-free-firmware
platform/installers/debian/sources.list:14:# forky-backports
platform/installers/debian/sources.list:15:deb http://deb.debian.org/debian forky-backports main contrib non-free non-free-firmware
platform/installers/debian/sources.list:16:deb-src http://deb.debian.org/debian forky-backports main contrib non-free non-free-firmware
platform/iso/.disk/info:1:Debian GNU/Linux none "Forky" - Snapshot amd64 LIVE/INSTALL Binary 20260120-18:28
platform/iso/.disk/mkisofs:1:xorriso -as mkisofs -R -r -J -joliet-long -l -cache-inodes -iso-level 3 -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin -partition_offset 16 -A "Debian Live" -p "live-build 20250814; https://salsa.debian.org/live-team/live-build" -publisher "Debian Live project; https://wiki.debian.org/DebianLive; debian-live@lists.debian.org" -V "Debian forky 20260120-18:28" --modification-date=2026012023285400 -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat -isohybrid-apm-hfsplus -o live-image-amd64.hybrid.iso binary
platform/packaging/dists/forky/Release:2:Codename: forky
platform/packaging/dists/forky/Release:8:Suite: forky
sources.list:2:# forky sources.list
sources.list:4:## forky
sources.list:5:deb http://deb.debian.org/debian forky main contrib non-free non-free-firmware
sources.list:6:deb-src http://deb.debian.org/debian forky main contrib non-free non-free-firmware
sources.list:8:## forky-updates
sources.list:9:deb http://deb.debian.org/debian forky-updates main contrib non-free non-free-firmware
sources.list:10:deb-src http://deb.debian.org/debian forky-updates main contrib non-free non-free-firmware
sources.list:12:## forky-security
sources.list:13:deb http://security.debian.org/debian-security forky-security main contrib non-free non-free-firmware
sources.list:14:deb-src http://security.debian.org/debian-security forky-security main contrib non-free non-free-firmware
sources.list:16:## forky-backports
sources.list:17:# deb http://deb.debian.org/debian forky-backports main contrib non-free non-free-firmware
sources.list:18:# deb-src http://deb.debian.org/debian forky-backports main contrib non-free non-free-firmware
src/huey/memory/DOCKER/Dockerfile:1:# Base: Python 3.12 on Debian Forky (good wheel coverage / stability)
src/huey/memory/DOCKER/Dockerfile:2:FROM python:3.12-forky
src/huey/memory/MD/HARDWARE.md:1:# Hardware Enablement Guide ΓÇö Huey OS (Forky Standard ┬╖ HueyOS 7.0 Kernel Family)
src/huey/memory/MD/HARDWARE.md:11:**OS Base**: Debian ΓÇ£ForkyΓÇ¥ (standardized baseline)
src/huey/memory/MD/HARDWARE.md:14:> **Current state:** Hardware enablement is standardized on the **Forky + 7.0 kernel family** line.  
src/huey/memory/MD/os-debloating.md:15:## Debian Forky
src/huey/memory/MD/os-debloating.md:17:While no automatic script is supplied for Linux, you can achieve a lightweight Forky installation by uninstalling packages you do not require and disabling unused services:
src/huey/memory/PY/system_checks.py:35:_SUPPORTED_LINUX_CODENAMES = {"forky", "testing"}
src/huey/memory/PY/system_checks.py:113:                "Unsupported Linux distribution detected (%s %s). Debian Forky/testing is required.",
src/huey/memory/PY/update_sources_to_forky.py:5:# HueyOS: Update Sources To Forky module (huey/memory/PY)
src/huey/memory/PY/update_sources_to_forky.py:17:By default the script switches all repository entries to ``forky`` but a
src/huey/memory/PY/update_sources_to_forky.py:30:DEFAULT_RELEASE = "forky"
src/huey/memory/PY/update_sources_to_trixie.py:18:use ``update_sources_to_forky.py`` instead. A different release codename may
src/huey/memory/SH/Huey.sh:16:# Huey.sh - Prepare a Debian Forky environment and
src/huey/memory/SH/Huey.sh:33:    local codename="${DEBIAN_CODENAME:-forky}"
src/huey/memory/SH/Huey.sh:35:    python3 "$(dirname "$0")/scripts/update_sources_to_forky.py" "$codename" || true
src/huey/memory/SH/build_huey_iso.sh:12:# for Debian Forky.
src/huey/memory/SH/build_huey_iso.sh:129:# --- live-build config (UEFI-only, amd64, Debian Forky) ---
src/huey/memory/SH/build_huey_iso.sh:136:  --distribution forky \
src/huey/memory/SH/build_huey_iso.sh:166:UEFI-only, amd64. Kernel 7.0.x${LOCALVER}. Profile: ${PROFILE}. Custom Debian Forky live + installer image for Monkey-Head-Project.
src/huey/memory/SH/upgrade_to_forky.sh:9:suite="forky"
src/huey/memory/SH/upgrade_to_forky.sh:24:  tmp_file="${file}.forky"
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:241:* The software baseline is Debian 14 Forky, Python 3.13.x, PyGPT-net, and Ollama.
src/huey/memory/YAML/config.yaml:13:  os: 'debian-forky'
src/huey/memory/YML/docker-compose.yml:41:        DEBIAN_VERSION: "forky"
src/huey/memory/YML/docker-compose.yml:75:    image: debian:forky
src/huey/prompts/master-plan-v2-final.json:83:    "base": "Debian 14 (Forky preferred, Trixie migration-only)",
src/huey/prompts/master-plan-v3.json:90:      "primary": "Debian 14 (Forky)",
src/huey/prompts/master-plan-v3.json:91:      "testing": "Debian 14 (Forky) on selected nodes",
src/huey/prompts/master-plan-v3.json:136:        "hardware": "ASUS 2-in-1 N4500 (LTE, touchscreen), dual-boot Windows 11 + Debian Forky"
src/huey/prompts/master-plan-v3.json:141:        "hardware": "iMac 5K 2017 running Debian Forky"
src/huey/prompts/master-plan-v5.json:106:      "primary": "Debian 14 (Forky)",
src/huey/prompts/master-plan-v5.json:107:      "testing": "Debian 14 (Forky) on selected nodes",
src/huey/prompts/master-plan-v5.json:152:        "hardware": "ASUS 2-in-1 N4500 (LTE, touchscreen), dual-boot Windows 11 + Debian Forky"
src/huey/prompts/master-plan-v5.json:157:        "hardware": "iMac 5K 2017 running Debian Forky"
src/huey/system_checks.py:27:SUPPORTED_DISTRO_CODENAME = "forky"
src/huey/system_checks.py:166:            "Unsupported Linux distribution detected (%s %s). Debian Forky is required.",
tests/test_os_check.py:29:        patch("distro.codename", return_value="forky"),
tests/test_os_check_fallback.py:17:            return_value={"ID": "debian", "VERSION_CODENAME": "forky"},

## Python 3.13

.github/workflows/package-smoke.yml:20:      - name: Set up Python 3.13
.github/workflows/release-dry-run.yml:24:      - name: Set up Python 3.13
Makefile:2:# Target baseline: Python 3.13.x
README.md:895:| Python 3.13.x | Day-to-day scripting/runtime baseline |
docs/audits/v101.1-stabilization-final.md:38:- PASS: `python --version` ΓåÆ Python 3.13.13.
docs/runbooks/huey-brain-v1-legion-go.md:16:## 1) Python 3.13 setup
docs/unsorted/phase-9-rollback.md:13:- Result: Python 3.13.3 was selected via `pyenv`, the virtual environment was created successfully, and activation succeeded. `pip install -e . '.[ml,data,cloud]'` failed with `ResolutionImpossible` because the extras have mutually incompatible pinned dependencies in this repository revision.
master-plan-v101.1.json:6:  "description": "Master Plan V101.1: PyHuey cockpit alignment release. V101.1 preserves the V101.0 Legion Go / Huey Brain V1 scope lock while adding PyHuey as the project-controlled fork of PyGPT and the Windows 11 Pro cockpit/build/runtime surface for Huey. It standardizes repository paths around integrations/pyhuey and platform/windows/huey, records Python 3.13 as the Windows Huey/PyHuey target branch, keeps Windows/PyHuey out of Huey Brain sovereignty, and treats docs, website, GitHub/README, and the master plan as the human-readable build-record surfaces.",
master-plan-v101.1.json:9:  "source_basis": "Updated from master-plan-v101.0.json and README-v101.0.md with current-session PyHuey cockpit decision, Windows 11 Pro on Huey Python 3.13 build proof, patched Redis vector-store overlay proof, and repository path normalization around integrations/pyhuey and platform/windows/huey.",
master-plan-v101.1.json:433:      "observed_gap": "v101.1 updates the v101.0 README/master plan basis with PyHuey naming, Windows Huey path normalization, and Python 3.13 cockpit build proof."
master-plan-v101.1.json:446:      "platform/windows/huey": "Windows 11 Pro build/runtime material, local modifications, launch/build scripts, patched wheels, freezes, and Python 3.13 branch record.",
master-plan-v101.1.json:603:      "responsibility": "provide controlled Windows cockpit, provider/tool testing, PyGPT-derived interface work, Redis/vector-store patch experimentation, launch/build scripts, and reproducible Python 3.13 freezes.",
master-plan-v101.1.json:644:      "python": "Python 3.13.x baseline unless current machine proves otherwise",
master-plan-v101.1.json:662:      "python": "Python 3.13.x target branch; current proof used Python 3.13.13 in Venvs/PyGPT.",
master-plan-v101.1.json:666:      "dependency_policy": "wheel-first, compiler-second; patch old pins to Python 3.13 wheel-supported versions; preserve freezes and pip-check records.",
master-plan-v101.1.json:1033:    "v101_1_decision": "Fork PyGPT as PyHuey. Use PyHuey for the project cockpit and controlled Windows 11 Pro Python 3.13 branch. Keep PyGPT/PyGPT-net as upstream/source-lineage terminology.",
master-plan-v101.1.json:2591:      "PyHuey": "forked PyGPT cockpit, Python 3.13 Windows branch, controlled update cycle",
master-plan-v101.1.json:2597:      "Python 3.13 is the Windows Huey/PyHuey target.",
master-plan-v101.1.json:2601:      "Patch old dependency pins to Python 3.13 wheel-supported versions when possible.",
master-plan-v101.1.json:2695:    "python_target": "Python 3.13.x; current validated branch used Python 3.13.13",
master-plan-v101.1.json:2705:      "baseline": "Python 3.13 PyGPT/PyHuey venv reached pip check clean and passed core import tests.",
master-plan-v101.1.json:2714:    "update_policy": "Control the update cycle through the PyHuey fork. Upstream PyGPT changes should be pulled deliberately, tested against the Windows 11 Pro/Python 3.13 branch, and tagged before promotion."
master-plan-v101.1.json:2729:    "Windows 11 Pro on Huey is the PyHuey cockpit/build/runtime surface using the Python 3.13 branch.",
master-plan-v101.1.json:2738:    "new_active_cockpit": "PyHuey on Windows 11 Pro / Python 3.13.",
master-plan-v101.1.json:2742:  "change_log_v101_1": "Added PyHuey cockpit naming, Windows 11 Pro/Python 3.13 branch posture, repository paths integrations/pyhuey and platform/windows/huey, and Redis-vector overlay proof status while preserving Huey Brain V1 scope lock."
platform/packaging/dists/forky/main/binary-amd64/Packages:2597: This package contains Python 3.13's standard library. It is normally not
src/huey/memory/PY/system_checks.py:132:            "Python 3.%s detected. Supported versions are Python 3.13 and 3.14.",
src/huey/memory/TXT/01 - Thesis_Ethos_Method_Proofcase.txt:241:* The software baseline is Debian 14 Forky, Python 3.13.x, PyGPT-net, and Ollama.
src/huey/memory/TXT/02 - Cornerstone_&_Pillars.txt:212:   When a project line is drawn around a runtime, that becomes a Pillar. For example, a communication layer that depends on Python 3.13.x means that surrounding software must adapt to that line rather than casually forcing the system backward or sideways.
src/huey/prompts/master-plan-v2-final.json:93:    "runtime": "Python 3.13.x",
tests/test_system_checks_module.py:71:    assert "Python 3.13" not in caplog.text

## Python 3.14

docs/unsorted/python314-upgrade-notes.md:1:# Python 3.14 Upgrade Attempt
docs/unsorted/python314-upgrade-notes.md:3:The Phase 4 task to install Python 3.14 and rebuild the HueyOS virtual environment could not be completed because the Ubuntu package repositories in this environment do not provide the requested packages.
docs/unsorted/python314-upgrade-notes.md:23:Without the Python 3.14 runtime the subsequent virtual environment creation step also fails:
docs/unsorted/python314-upgrade-notes.md:30:As soon as Ubuntu packages for Python 3.14 are published, rerunning the commands above should allow the environment rebuild to proceed.
platform/installers/debian/Debian/install-deb.sh:310:Python 3.14.x is required for the Monkey Head Project runtime but was not detected.
platform/installers/debian/Debian/install-deb.sh:313:Install Python 3.14 from your distribution (preferred) or build CPython 3.14.x from source.
platform/installers/debian/Debian/install-deb.sh:330:Re-run this installer after Python 3.14 is available (python3.14).
platform/installers/debian/Debian/update-deb.sh:243:Python 3.14.x is required for the Monkey Head Project runtime.
platform/installers/debian/Debian/update-deb.sh:247:Python 3.14 is available and rebuild the virtual environment.
