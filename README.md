# FSN: high-temperature fast breeder reactor study

Physics-first exploration of fast-spectrum breeder reactors that deliver heat at 850 °C and above, for electricity or direct industrial use. Regulation and cost are out of scope for now.

**Start here: [docs/README.md](docs/README.md)**: map of the problem space, designs, materials, studies and decisions.

| Area | Where |
| --- | --- |
| Project brief, targets, roadmap | [docs/project/](docs/project/) |
| Design taxonomy and materials screening method | [docs/framework/](docs/framework/) |
| Candidate designs (one page each) | [docs/designs/](docs/designs/README.md) |
| Materials (one page each, facts from the database) | [docs/materials/](docs/materials/README.md) |
| Studies (cross-cutting analyses) | [docs/studies/](docs/studies/README.md) |
| Decisions | [docs/decisions/](docs/decisions/README.md) |
| Open questions and go/no-go tests | [docs/open-questions.md](docs/open-questions.md) |
| Property database (code, sources, usage) | [docs/data/database.md](docs/data/database.md), package `htfbr_data/` |

```bash
bash setup/install_env.sh && export PATH=/opt/mamba/envs/nuc/bin:$PATH
htfbr-data build          # build the property database from primary sources
htfbr-data docs           # regenerate doc indexes and database facts in material pages
python -m pytest          # code tests, plus doc link and index checks
```
