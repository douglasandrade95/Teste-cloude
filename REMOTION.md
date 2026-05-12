# REMOTION - React-Based Video Rendering Framework

Uma documentação separada para usar Remotion como tecnologia de renderização de vídeo.

## 🎯 Visão Geral do Projeto

Remotion é um framework React para renderizar vídeos de forma programática. Diferente do FastAPI + MoviePy (processamento de vídeos existentes), Remotion gera vídeos do zero usando componentes React.

## 🏗️ Fundação do Projeto

O arquivo raiz (`src/Root.tsx`) define composições com propriedades como:
- **Duration**: Duração em frames
- **Dimensions**: Resolução (padrão 1920x1080)
- **Frame rate**: FPS (padrão 30)

## 🎬 Estrutura de Componentes

Os componentes usam hooks como `useCurrentFrame()` para acessar o número do frame (começando em 0).

### Tags Especializadas

**Vídeo:**
```tsx
<OffthreadVideo 
  src="..." 
  startFrom={100}
  endAt={500}
  volume={0.8}
/>
```

**Imagens:**
```tsx
<Img src={staticFile('image.png')} />
<Gif src={staticFile('animation.gif')} /> // de "@remotion/gif"
```

**Áudio:**
```tsx
<Audio 
  src="..." 
  startFrom={0}
  endAt={1000}
  volume={1}
/>
```

**Camadas:**
```tsx
<AbsoluteFill>
  {/* Elementos sobrepostos */}
</AbsoluteFill>
```

Fontes de assets suportam URLs remotas ou arquivos locais via `staticFile()`.

## ⏱️ Timing e Animação

**Sequenciamento:**
```tsx
<Sequence from={0} durationInFrames={100}>
  <Componente />
</Sequence>

<Series>
  <Componente1 />
  <Componente2 />
  {/* Encadeamento automático */}
</Series>
```

**Transições:**
```tsx
<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={30}>
    <Componente1 />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition 
    presentation={slide}
    durationInFrames={15}
  />
  <TransitionSeries.Sequence durationInFrames={30}>
    <Componente2 />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

**Helpers de Animação:**
```tsx
// Interpolação linear
const opacity = interpolate(
  frame,
  [0, 30],
  [0, 1]
);

// Animação com spring physics
const scale = spring({
  frame,
  config: { damping: 5 }
});

// Valores determinísticos (não Math.random())
const randomValue = random('chave-única');
```

## ⚠️ Princípio de Design Crítico

> "Componentes Remotion não podem ter interações do usuário. Devem ser determinísticos."

Remotion é **fundamentalmente uma ferramenta de geração de vídeo**, não uma interface interativa. Todas as animações derivam de números de frames, não de estado ou eventos.

### Implicações:
- ❌ Sem `onClick`, `onChange`, hooks de estado
- ✅ Tudo baseado em `useCurrentFrame()`
- ✅ Comportamento idêntico em cada render

## 🔄 Quando Usar Remotion vs. MoviePy

| Caso | Remotion | MoviePy |
|------|----------|---------|
| Gerar vídeos do zero | ✅ | ❌ |
| Processar vídeos existentes | ❌ | ✅ |
| Efeitos dinâmicos | ✅ | ⚠️ |
| Títulos/gráficos animados | ✅ | ❌ |
| Renderização paralela | ✅ | ⚠️ |

## 📦 Assets e Recursos

Coloque arquivos de mídia em `public/` e acesse com:

```tsx
import { staticFile } from 'remotion';

<Img src={staticFile('images/banner.png')} />
```

## 🚀 Próximos Passos

Para integrar Remotion ao AutoVideoEditor, considere:

1. **Componentes Reutilizáveis**: Criar templates de Reels/TikTok/Shorts
2. **Parametrização**: Props para customizar cores, textos, músicas
3. **Renderização**: Usar Remotion para gerar vídeos a partir da análise do Claude
4. **Performance**: Otimizar para renderização em batch (múltiplos vídeos)

---

**Referência:** Este arquivo documenta Remotion de forma separada do projeto principal AutoVideoEditor. Use quando precisar gerar novos vídeos em vez de processar vídeos existentes.
