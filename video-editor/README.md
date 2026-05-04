# Video Editor - Remotion

Um editor de vídeo moderno e intuitivo construído com React e Remotion.

## Funcionalidades

✨ **Timeline Interativa**
- Controle preciso de tempo com scrubber
- Visualização de clipes em tempo real
- Playhead indicador de posição

🎬 **Tipos de Clipes Suportados**
- Texto com customização
- Imagens/Fotos
- Vídeos integrados

⚙️ **Controles Avançados**
- Adicionar/remover clipes facilmente
- Edição de duração
- Gerenciamento de camadas (z-index)

🎨 **Interface Moderna**
- Dark mode por padrão
- Design responsivo
- Feedback visual ao interagir

## Estrutura

```
video-editor/
├── VideoEditor.jsx    # Componente principal do editor
├── styles.css         # Estilos do editor
├── package.json       # Dependências
└── README.md          # Este arquivo
```

## Componentes Principais

### VideoEditor
Componente principal que gerencia:
- Estado dos clipes
- Timeline e scrubber
- Controles de adição/remoção de clipes

### VideoPreview
Renderiza o vídeo com todos os clipes aplicados

### TimelineTrack
Visualiza os clipes na timeline com scrubber

## Uso

```jsx
import VideoEditor from './VideoEditor';

export default VideoEditor;
```

## Dependências

- **React** - Framework UI
- **Remotion** - Renderização de vídeos

## Instalação

```bash
npm install
```

## Próximas Funcionalidades

- [ ] Efeitos de transição
- [ ] Filtros de cor
- [ ] Áudio/Música de fundo
- [ ] Exportação de vídeo
- [ ] Undo/Redo
- [ ] Keyframes e animações
- [ ] Drag and drop na timeline
- [ ] Recorte de clipes
- [ ] Múltiplas faixas de áudio

## Performance

- Renderização otimizada com Remotion
- Cache de composições
- Atualização incremental de timeline

## Acessibilidade

- Suporte a teclado
- Feedback visual clara
- Cores contrastantes

## Licença

MIT
