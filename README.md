# Judex

Ferramenta para extração de dados jurídicos do STF (Supremo Tribunal Federal).

## Instalação

```bash
pip install judex
```

## Uso

```python
from judex import StfSpider, init_database

# Inicializar banco de dados
init_database("casos.db")

# Executar spider
spider = StfSpider()
# ... configurar e executar
```
## Licença

MIT
