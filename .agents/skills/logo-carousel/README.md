# Logo Carousel Skill

Um agent skill para criar e gerenciar carrosséis animados de logos em React.

## Estrutura do Skill

```
logo-carousel/
├── SKILL.md              # Definição e instruções do skill
├── example-clients.json  # Exemplo de dados de clientes
├── styles.css            # Estilos CSS reutilizáveis
└── README.md             # Este arquivo
```

## Arquivos do Skill

### SKILL.md
Contém:
- Metadados (name, description)
- Instruções completas para criar um carrossel de logos
- Exemplo de componente React
- Guia de customização
- Informações sobre suporte a dark mode

### example-clients.json
Um exemplo de array de dados de clientes que pode ser usado como template para a estrutura de dados esperada pelo componente.

### styles.css
Estilos CSS prontos para usar que incluem:
- Animação de scroll infinito
- Suporte a dark mode
- Estilos responsivos
- Acessibilidade (focus states)

## Como Usar este Skill

1. **Descoberta**: O agente carrega o skill e vê seu nome e descrição
2. **Ativação**: Quando você pede para criar um carrossel, o agente carrega o SKILL.md completo
3. **Execução**: O agente segue as instruções para criar o componente React

## Compatibilidade

Este skill é compatível com:
- GitHub Copilot (VS Code)
- Claude Code
- OpenAI Codex
- Qualquer outro agente que suporte Agent Skills

## Componentes Principais

- **LogoCarousel**: Componente React que renderiza o carrossel
- **clients**: Array de objetos com dados dos logos
- **Animação CSS**: `logo-scroll` - animação linear infinita

## Customizações Suportadas

- Velocidade de scroll (PX_PER_SECOND)
- Espaçamento entre logos (GAP_PX)
- Escala individual de logos (propriedade scale)
- Temas claro/escuro (lightSrc/darkSrc)
- Links personalizados (url)
