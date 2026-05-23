import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './styles.css';

const HEALTH_LABELS = {
  covered: 'coperto',
  partial: 'parziale',
  missing: 'manca',
  idea: 'idea',
};

const VIEWS = {
  design: { label: 'Design App', origin: ['design'], fallbackLayers: ['frontend', 'product'], edgeKinds: ['navigates', 'triggers', 'calls_api', 'uses_data', 'calls'] },
  code: { label: 'Codice rilevato', origin: ['code', 'scanner'], edgeKinds: [] },
  gap: { label: 'Gap', gapOnly: true, edgeKinds: [] },
  audit: { label: 'Problemi', auditOnly: true, edgeKinds: [] },
  flows: { label: 'Flussi', flowOnly: true, edgeKinds: [] },
  build: { label: 'Costruzione', layers: ['frontend', 'backend', 'data', 'qa'], edgeKinds: ['navigates', 'triggers', 'calls_api', 'uses_data', 'verifies'] },
  full: { label: 'Tutto', layers: [], edgeKinds: [] },
};

const AUDIT_LABELS = {
  rotto: 'Da sistemare',
  debole: 'Da verificare',
  probabile: 'Sembra corretto',
  certo: 'Confermato',
};

const LAYER_LABELS = {
  product: 'Prodotto',
  frontend: 'Schermate',
  backend: 'Backend',
  data: 'Dati',
  qa: 'Test',
  devops: 'Runtime',
  docs: 'Documenti',
};

function esc(value) {
  return String(value ?? '');
}

function BlueprintNode({ data, selected }) {
  const health = data.health || 'idea';
  return (
    <div className={`bf-node bf-node-${health} bf-layer-${data.layer || 'product'} bf-origin-${data.origin || 'scanner'} bf-gap-${data.gapStatus || 'ok'} bf-audit-${data.auditStatus || 'debole'} ${selected ? 'is-selected' : ''}`}>
      <Handle type="target" position={Position.Left} className="bf-handle" />
      <div className="bf-node-header">
        <span>{data.kind || data.domain || 'nodo'}</span>
        <strong>{data.auditStatus ? AUDIT_LABELS[data.auditStatus] || data.auditStatus : data.gapStatus && data.gapStatus !== 'ok' ? data.gapStatus : data.origin || data.layer || HEALTH_LABELS[health] || health}</strong>
      </div>
      <div className="bf-node-title">{data.title}</div>
      <div className="bf-node-body">{data.summary}</div>
      <div className="bf-node-footer">
        {data.connectionCount} collegamenti{data.subnodes?.length ? ` / ${data.subnodes.length} sotto-nodi` : ''}{data.uiRoute || data.apiRoute ? ` / ${data.uiRoute || data.apiRoute}` : ''}
      </div>
      {data.childCount ? (
        <button
          type="button"
          className="bf-node-toggle"
          onClick={(event) => {
            event.stopPropagation();
            data.onToggleParent?.(data.id);
          }}
        >
          {data.isExpanded ? 'Chiudi dettagli' : `Apri ${data.childCount}`}
        </button>
      ) : null}
      <Handle type="source" position={Position.Right} className="bf-handle" />
    </div>
  );
}

const nodeTypes = { blueprint: BlueprintNode };

function readPayload(root) {
  const script = root.querySelector('script[type="application/json"]');
  if (!script) return { nodes: [], edges: [], projectPath: '', domains: [] };
  try {
    return JSON.parse(script.textContent || '{}');
  } catch {
    return { nodes: [], edges: [], projectPath: '', domains: [] };
  }
}

function toFlowNode(node, connectionCount = 0) {
  return {
    id: esc(node.id),
    type: 'blueprint',
    position: { x: Number(node.x || 0), y: Number(node.y || 0) },
    data: {
      ...node,
      title: esc(node.title),
      summary: esc(node.summary || node.description),
      connectionCount,
    },
  };
}

function toFlowEdge(edge) {
  const confidence = edge.confidence || 'suggested';
  const state = edge.state || (confidence === 'high' ? 'confirmed' : 'proposed');
  return {
    id: esc(edge.id),
    source: esc(edge.source),
    target: esc(edge.target),
    label: esc(edge.label || 'parla con'),
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed },
    data: edge,
    className: `bf-edge-${confidence === 'high' ? 'high' : 'suggested'} bf-edge-state-${state}`,
  };
}

function applyEdgeMode(edges, mode) {
  return edges.map((edge) => {
    const confidence = edge.data?.confidence || 'suggested';
    const visible =
      mode === 'all' ||
      (mode === 'certain' && confidence === 'high') ||
      (mode === 'suggested' && confidence !== 'high');
    return { ...edge, hidden: mode === 'none' || !visible };
  });
}

function applyView(nodes, edges, view) {
  const config = VIEWS[view] || VIEWS.full;
  if (view === 'full') {
    return {
      nodes: nodes.map((node) => ({ ...node, hidden: false })),
      edges,
    };
  }
  const baseIds = new Set(
    nodes
      .filter((node) => {
        if (config.gapOnly) return ['missing_code', 'broken'].includes(node.data?.gapStatus);
        if (config.auditOnly) return Boolean(node.data?.auditProblem) || ['rotto', 'debole'].includes(node.data?.auditStatus);
        if (config.flowOnly) return false;
        if (config.origin) return config.origin.includes(node.data?.origin);
        return config.layers.includes(node.data?.layer);
      })
      .map((node) => node.id),
  );
  if (!baseIds.size && config.fallbackLayers) {
    nodes
      .filter((node) => config.fallbackLayers.includes(node.data?.layer))
      .forEach((node) => baseIds.add(node.id));
  }
  const visibleEdgeIds = new Set();
  edges.forEach((edge) => {
    const kind = edge.data?.kind || 'calls';
    const touchesBase = baseIds.has(edge.source) || baseIds.has(edge.target);
    if (touchesBase && (!config.edgeKinds.length || config.edgeKinds.includes(kind))) {
      visibleEdgeIds.add(edge.id);
      baseIds.add(edge.source);
      baseIds.add(edge.target);
    }
  });
  return {
    nodes: nodes.map((node) => ({ ...node, hidden: !baseIds.has(node.id) })),
    edges: edges.map((edge) => ({ ...edge, hidden: edge.hidden || !visibleEdgeIds.has(edge.id) })),
  };
}

function FlowBoard({ root }) {
  const payload = useMemo(() => readPayload(root), [root]);
  const boardView = payload.blueprintView || {};
  const flowNodeIds = useMemo(() => {
    const ids = new Set();
    (payload.flows || []).forEach((flow) => (flow.node_ids || []).forEach((id) => ids.add(String(id))));
    return ids;
  }, [payload.flows]);
  const initialEdges = useMemo(() => payload.edges.map(toFlowEdge), [payload.edges]);
  const edgeCounts = useMemo(() => {
    const counts = {};
    initialEdges.forEach((edge) => {
      counts[edge.source] = (counts[edge.source] || 0) + 1;
      counts[edge.target] = (counts[edge.target] || 0) + 1;
    });
    return counts;
  }, [initialEdges]);
  const initialNodes = useMemo(() => payload.nodes.map((node) => toFlowNode(node, edgeCounts[esc(node.id)] || 0)), [payload.nodes, edgeCounts]);
  const defaultMode = initialEdges.some((edge) => edge.data?.confidence === 'high') ? 'certain' : 'suggested';
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(applyEdgeMode(initialEdges, defaultMode));
  const [lineMode, setLineMode] = useState(defaultMode);
  const defaultView = boardView.issues?.length ? 'audit' : flowNodeIds.size ? 'flows' : 'build';
  const [viewMode, setViewMode] = useState(defaultView);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');
  const [selectedId, setSelectedId] = useState(initialNodes[0]?.id || '');
  const [saveLabel, setSaveLabel] = useState('Salva layout');
  const [feedbackLabel, setFeedbackLabel] = useState('');
  const [taskLabel, setTaskLabel] = useState('');
  const [expandedParents, setExpandedParents] = useState(() => new Set());
  const previewRef = useRef(null);
  const flow = useReactFlow();

  const childrenByParent = useMemo(() => {
    const grouped = new Map();
    nodes.forEach((node) => {
      const parentId = node.data?.parentId;
      if (!parentId) return;
      if (!grouped.has(parentId)) grouped.set(parentId, []);
      grouped.get(parentId).push(node.id);
    });
    return grouped;
  }, [nodes]);

  const childIndexById = useMemo(() => {
    const indexes = new Map();
    childrenByParent.forEach((children) => {
      children.forEach((childId, index) => indexes.set(childId, index));
    });
    return indexes;
  }, [childrenByParent]);

  const toggleParent = useCallback((parentId) => {
    setExpandedParents((current) => {
      const next = new Set(current);
      if (next.has(parentId)) next.delete(parentId);
      else next.add(parentId);
      return next;
    });
  }, []);

  const viewFiltered = useMemo(() => {
    if (viewMode !== 'flows') return applyView(nodes, applyEdgeMode(edges, lineMode), viewMode);
    return {
      nodes: nodes.map((node) => ({ ...node, hidden: !flowNodeIds.has(node.id) })),
      edges: applyEdgeMode(edges, lineMode).map((edge) => ({ ...edge, hidden: !flowNodeIds.has(edge.source) || !flowNodeIds.has(edge.target) })),
    };
  }, [nodes, edges, lineMode, viewMode, flowNodeIds]);

  const visibleNodes = useMemo(() => {
    const term = search.trim().toLowerCase();
    return viewFiltered.nodes.map((node) => {
      const text = `${node.data.title} ${node.data.summary} ${node.data.description}`.toLowerCase();
      const parentCollapsed = node.data?.parentId && !expandedParents.has(node.data.parentId) && !term;
      const match = !node.hidden && !parentCollapsed && (!term || text.includes(term)) && (!domain || node.data.domain === domain);
      const childCount = childrenByParent.get(node.id)?.length || 0;
      const parentNode = node.data?.parentId ? nodes.find((item) => item.id === node.data.parentId) : null;
      const childIndex = childIndexById.get(node.id) || 0;
      const expandedPosition = parentNode && expandedParents.has(node.data.parentId)
        ? {
            x: parentNode.position.x + 310,
            y: parentNode.position.y + childIndex * 155 - Math.min(220, Math.max(0, (childrenByParent.get(node.data.parentId)?.length || 1) - 1) * 55),
          }
        : node.position;
      return {
        ...node,
        position: expandedPosition,
        hidden: !match,
        data: {
          ...node.data,
          childCount,
          isExpanded: expandedParents.has(node.id),
          onToggleParent: toggleParent,
        },
      };
    });
  }, [viewFiltered.nodes, search, domain, expandedParents, childrenByParent, childIndexById, nodes, toggleParent]);

  const visibleNodeIds = useMemo(
    () => new Set(visibleNodes.filter((node) => !node.hidden).map((node) => node.id)),
    [visibleNodes],
  );

  const visibleEdges = useMemo(
    () =>
      viewFiltered.edges.map((edge) => ({
        ...edge,
        hidden: edge.hidden || !visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target),
      })),
    [viewFiltered.edges, visibleNodeIds],
  );

  const selectedNode = visibleNodes.find((node) => node.id === selectedId) || visibleNodes.find((node) => !node.hidden);
  const preview = payload.preview || {};

  useEffect(() => {
    if (!selectedNode?.id || !previewRef.current?.contentWindow) return;
    previewRef.current.contentWindow.postMessage({ type: 'highlight-node', id: selectedNode.id }, '*');
  }, [selectedNode]);

  useEffect(() => {
    const receivePreviewSelection = (event) => {
      if (event.data?.type !== 'preview-node-click' || !event.data.id) return;
      const nextId = String(event.data.id);
      const node = nodes.find((item) => item.id === nextId);
      if (node?.data?.parentId) {
        setExpandedParents((current) => new Set(current).add(node.data.parentId));
      }
      setSelectedId(nextId);
    };
    window.addEventListener('message', receivePreviewSelection);
    return () => window.removeEventListener('message', receivePreviewSelection);
  }, [nodes]);

  const selectedRelations = useMemo(() => {
    if (!selectedNode) return [];
    return visibleEdges
      .filter((edge) => !edge.hidden && (edge.source === selectedNode.id || edge.target === selectedNode.id))
      .map((edge) => {
        const otherId = edge.source === selectedNode.id ? edge.target : edge.source;
        const other = nodes.find((node) => node.id === otherId);
        const sourceNode = nodes.find((node) => node.id === edge.source);
        const targetNode = nodes.find((node) => node.id === edge.target);
        return {
          ...edge.data,
          otherTitle: other?.data?.title || otherId,
          sourceTitle: sourceNode?.data?.title || edge.source,
          targetTitle: targetNode?.data?.title || edge.target,
          sourceEvidence: sourceNode?.data?.scannerEvidence || '',
          targetEvidence: targetNode?.data?.scannerEvidence || '',
          sourceFiles: sourceNode?.data?.relatedFiles || [],
          targetFiles: targetNode?.data?.relatedFiles || [],
        };
      });
  }, [selectedNode, visibleEdges, nodes]);
  const selectedPlan = useMemo(() => {
    if (!selectedNode) return [];
    return (payload.auditPlan || []).filter((item) => item.node === selectedNode.data?.title);
  }, [payload.auditPlan, selectedNode]);
  const selectedFlows = useMemo(() => {
    if (!selectedNode) return [];
    return (payload.flows || []).filter((item) => (item.node_ids || []).includes(selectedNode.id));
  }, [payload.flows, selectedNode]);

  const visibleStats = useMemo(() => {
    const visible = visibleNodes.filter((node) => !node.hidden);
    return {
      design: visible.filter((node) => node.data.origin === 'design').length,
      code: visible.filter((node) => ['code', 'scanner'].includes(node.data.origin)).length,
      gaps: visible.filter((node) => node.data.gapStatus && node.data.gapStatus !== 'ok').length,
      problems: visible.filter((node) => node.data.auditProblem || node.data.auditStatus === 'rotto').length,
    };
  }, [visibleNodes]);

  const boardHome = useMemo(() => {
    const issues = boardView.issues || [];
    const actions = boardView.actions || [];
    const stats = boardView.stats || {};
    const brokenFlows = (boardView.flows || payload.flows || []).filter((item) => item.status === 'rotto');
    const partialFlows = (boardView.flows || payload.flows || []).filter((item) => item.status === 'parziale');
    const completeFlows = (boardView.flows || payload.flows || []).filter((item) => item.status === 'completo');
    const realIssues = issues.filter((item) => item.issue_kind === 'real_issue');
    const hypotheses = issues.filter((item) => item.issue_kind === 'scanner_hypothesis');
    const confirmedNodes = nodes.filter((node) => node.data.auditStatus === 'certo');
    const firstFromIds = (ids = []) => ids.map((id) => nodes.find((node) => node.id === id)).find(Boolean);
    const firstByIssue = (issue) => nodes.find((node) => node.id === String(issue?.id || ''));
    return [
      {
        key: 'broken',
        label: 'Da sistemare',
        count: realIssues.length || brokenFlows.length,
        text: actions[0]?.action || realIssues[0]?.fix || brokenFlows[0]?.next_step || 'Nessun blocco evidente nella vista principale.',
        target: firstByIssue(realIssues[0]) || (brokenFlows[0] ? firstFromIds(brokenFlows[0].node_ids) : null),
      },
      {
        key: 'check',
        label: 'Da chiarire',
        count: hypotheses.length || partialFlows.length,
        text: hypotheses[0]?.reason || partialFlows[0]?.next_step || 'Nessun punto debole evidente nella vista principale.',
        target: firstByIssue(hypotheses[0]) || (partialFlows[0] ? firstFromIds(partialFlows[0].node_ids) : null),
      },
      {
        key: 'ok',
        label: 'Funziona',
        count: completeFlows.length || confirmedNodes.length,
        text: completeFlows[0]?.chain || `${stats.nodes_total || nodes.length} nodi nel modello operativo.`,
        target: completeFlows[0] ? firstFromIds(completeFlows[0].node_ids) : nodes.find((node) => node.data.auditStatus === 'certo'),
      },
      {
        key: 'noise',
        label: 'Rumore noto',
        count: stats.known_noise || 0,
        text: 'Controlli interni e segnali tecnici nascosti dalla vista principale.',
        target: null,
      },
    ];
  }, [payload.flows, boardView, nodes]);

  const boardPrimaryAction = useMemo(() => {
    const focus = boardView.focus || {};
    const action = (boardView.actions || [])[0] || {};
    const issue = (boardView.issues || [])[0] || {};
    const target =
      nodes.find((node) => node.id === String(issue.id || focus.id || '')) ||
      nodes.find((node) => node.data?.title === action.node) ||
      null;
    return {
      title: issue.title || focus.title || action.node || 'Nessun focus critico',
      action: action.action || issue.fix || focus.next_action || 'Continua dalla vista Flussi e verifica il prossimo nodo utile.',
      why: action.why || issue.reason || focus.reason || 'La Lavagna sta filtrando rumore tecnico e mostra solo il lavoro piu utile.',
      check: action.check || 'Rigenera la dashboard e verifica che la Lavagna riduca problemi o ipotesi aperte.',
      target,
    };
  }, [boardView, nodes]);

  const taskPrompt = useMemo(() => {
    if (!selectedNode) return '';
    const action = (boardView.actions || []).find((item) => item.node === selectedNode.data?.title);
    if (action?.task_prompt) return action.task_prompt;
    return [
      `Goal: ${selectedNode.data?.auditFix || selectedNode.data?.nextAction || 'Chiarire o sistemare questo nodo.'}`,
      `Nodo: ${selectedNode.data?.title || selectedNode.id}`,
      `Problema: ${selectedNode.data?.auditProblem || selectedNode.data?.auditStatus || 'da verificare'}`,
      `Contesto minimo: ${selectedNode.data?.scannerEvidence || selectedNode.data?.summary || ''}`,
      `File: ${(selectedNode.data?.relatedFiles || []).slice(0, 5).join(', ') || 'da individuare'}`,
      'Check: rigenera la dashboard e verifica che lo stato della Lavagna migliori.',
      'Non toccare codice non collegato a questo nodo.',
    ].join('\n');
  }, [boardView.actions, selectedNode]);

  const setMode = useCallback(
    (mode) => {
      setLineMode(mode);
      setEdges((current) => applyEdgeMode(current, mode));
    },
    [setEdges],
  );

  const saveLayout = useCallback(async () => {
    const positions = {};
    nodes.forEach((node) => {
      positions[node.id] = { x: Math.round(node.position.x * 100) / 100, y: Math.round(node.position.y * 100) / 100 };
    });
    setSaveLabel('Salvo...');
    try {
      const response = await fetch('/blueprint-layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: payload.projectPath, positions }),
      });
      const result = await response.json();
      setSaveLabel(result.ok ? `Salvato (${result.saved})` : 'Errore');
    } catch {
      setSaveLabel('Errore');
    }
    window.setTimeout(() => setSaveLabel('Salva layout'), 1800);
  }, [nodes, payload.projectPath]);

  const sendLearningFeedback = useCallback(async (outcome) => {
    if (!selectedNode?.id) return;
    setFeedbackLabel('Registro...');
    const params = new URLSearchParams({
      project: payload.projectPath,
      item: selectedNode.id,
      outcome,
    });
    try {
      await fetch(`/learning-feedback?${params.toString()}`);
      setFeedbackLabel('Registrato');
    } catch {
      setFeedbackLabel('Errore');
    }
    window.setTimeout(() => setFeedbackLabel(''), 1600);
  }, [payload.projectPath, selectedNode]);

  const sendEdgeFeedback = useCallback(async (rel, outcome) => {
    const item = `${rel.source}->${rel.target}:${rel.kind || 'calls'}`;
    setFeedbackLabel('Registro...');
    const params = new URLSearchParams({
      project: payload.projectPath,
      item,
      outcome,
    });
    try {
      await fetch(`/learning-feedback?${params.toString()}`);
      setFeedbackLabel(outcome === 'confirm_edge' ? 'Collegamento confermato' : 'Collegamento ignorato');
    } catch {
      setFeedbackLabel('Errore');
    }
    window.setTimeout(() => setFeedbackLabel(''), 1800);
  }, [payload.projectPath]);

  const focusNode = useCallback((node) => {
    if (!node?.id) return;
    setSelectedId(node.id);
    flow.setCenter(node.position.x + 130, node.position.y + 75, { zoom: 1.05, duration: 450 });
  }, [flow]);

  const openSubnode = useCallback((item) => {
    if (!item?.id) return;
    const child = nodes.find((node) => node.id === item.id);
    if (child?.data?.parentId) {
      setExpandedParents((current) => new Set(current).add(child.data.parentId));
    }
    setSelectedId(item.id);
  }, [nodes]);

  const copyTaskPrompt = useCallback(async () => {
    if (!taskPrompt) return;
    try {
      await navigator.clipboard.writeText(taskPrompt);
      setTaskLabel('Prompt copiato');
    } catch {
      setTaskLabel('Copia non disponibile');
    }
    window.setTimeout(() => setTaskLabel(''), 1600);
  }, [taskPrompt]);

  return (
    <div className="bf-shell">
      <section className="bf-primary-action">
        <div>
          <span>Prossima azione</span>
          <h3>{boardPrimaryAction.title}</h3>
          <p>{boardPrimaryAction.action}</p>
          <small>{boardPrimaryAction.why}</small>
        </div>
        <div className="bf-primary-check">
          <strong>Check</strong>
          <p>{boardPrimaryAction.check}</p>
          <button type="button" onClick={() => focusNode(boardPrimaryAction.target)} disabled={!boardPrimaryAction.target}>Apri nodo</button>
        </div>
      </section>
      <div className="bf-home">
        {boardHome.map((item) => (
          <button key={item.key} type="button" className={`bf-home-card bf-home-${item.key}`} onClick={() => focusNode(item.target)} disabled={!item.target}>
            <span>{item.label}</span>
            <strong>{item.count}</strong>
            <small>{item.text}</small>
          </button>
        ))}
      </div>
      <div className="bf-toolbar">
        <div className="bf-tool-group bf-tool-search">
          <span>Cerca</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nodo, file, funzione o route" />
        </div>
        <div className="bf-tool-group">
          <span>Dettagli UI</span>
          <button type="button" onClick={() => setExpandedParents(new Set(childrenByParent.keys()))}>Apri tutti</button>
          <button type="button" onClick={() => setExpandedParents(new Set())}>Chiudi tutti</button>
        </div>
        <div className="bf-tool-group">
          <span>Vista</span>
          {Object.entries(VIEWS).map(([key, view]) => (
            <button key={key} type="button" className={viewMode === key ? 'is-active' : ''} onClick={() => setViewMode(key)}>
              {view.label}
            </button>
          ))}
        </div>
        <details className="bf-advanced-tools">
          <summary>Strumenti mappa</summary>
          <div className="bf-tool-group">
            <span>Linee</span>
            <button type="button" className={lineMode === 'certain' ? 'is-active' : ''} onClick={() => setMode('certain')}>Certe</button>
            <button type="button" className={lineMode === 'suggested' ? 'is-active' : ''} onClick={() => setMode('suggested')}>Suggerite</button>
            <button type="button" className={lineMode === 'all' ? 'is-active' : ''} onClick={() => setMode('all')}>Tutte</button>
            <button type="button" className={lineMode === 'none' ? 'is-active' : ''} onClick={() => setMode('none')}>Nessuna</button>
          </div>
          <div className="bf-tool-group">
            <span>Mappa</span>
            <button type="button" onClick={() => flow.zoomIn()}>Zoom +</button>
            <button type="button" onClick={() => flow.zoomOut()}>Zoom -</button>
            <button type="button" onClick={() => flow.fitView({ padding: 0.18 })}>Centra</button>
            <button type="button" onClick={saveLayout}>{saveLabel}</button>
          </div>
          <div className="bf-tool-group">
            <span>Area</span>
            {payload.domains.map((item) => (
              <button key={item} type="button" className={domain === item ? 'is-active' : ''} onClick={() => setDomain(domain === item ? '' : item)}>
                {LAYER_LABELS[item] || item}
              </button>
            ))}
          </div>
        </details>
      </div>
      <div className="bf-legend">
        <span><i className="bf-dot bf-dot-ok" />Confermato</span>
        <span><i className="bf-dot bf-dot-warn" />Da verificare</span>
        <span><i className="bf-dot bf-dot-bad" />Da sistemare</span>
        <span><i className="bf-line bf-line-solid" />linea certa</span>
        <span><i className="bf-line bf-line-dashed" />linea suggerita</span>
        <span><i className="bf-line bf-line-muted" />linea ignorata</span>
      </div>
      <div className="bf-layout">
        <div className="bf-canvas">
          <ReactFlow
            nodes={visibleNodes}
            edges={visibleEdges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={(_, node) => setSelectedId(node.id)}
            onNodeDragStart={(_, node) => setSelectedId(node.id)}
            fitView
            fitViewOptions={{ padding: 0.18 }}
            minZoom={0.22}
            maxZoom={2.4}
            panOnDrag
            zoomOnPinch
            zoomOnScroll
            zoomOnDoubleClick={false}
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
          >
            <Background color="#c8d4e2" gap={22} size={1} />
            <MiniMap pannable zoomable nodeStrokeWidth={3} />
            <Controls showInteractive={false} />
            <Panel position="top-left" className="bf-count">
              {visibleNodes.filter((node) => !node.hidden).length} nodi / design {visibleStats.design} / codice {visibleStats.code} / problemi {visibleStats.problems} / gap {visibleStats.gaps}
            </Panel>
          </ReactFlow>
        </div>
        <div className="bf-side">
          <section className="bf-preview">
            <div className="bf-preview-head">
              <div>
                <span>Frontend</span>
                <strong>{preview.label || 'Preview UI'}</strong>
              </div>
              {preview.generatedUrl && preview.url !== preview.generatedUrl && (
                <button type="button" onClick={() => { previewRef.current.src = preview.generatedUrl; }}>Fallback</button>
              )}
            </div>
            {preview.url ? (
              <iframe
                ref={previewRef}
                title="Preview frontend progetto"
                src={preview.url}
                className="bf-preview-frame"
                onLoad={() => selectedNode?.id && previewRef.current?.contentWindow?.postMessage({ type: 'highlight-node', id: selectedNode.id }, '*')}
              />
            ) : (
              <p className="bf-empty">Nessuna preview frontend disponibile per questo progetto.</p>
            )}
          </section>
          <aside className="bf-detail">
          <div className="bf-detail-kicker">{selectedNode?.data?.origin || 'nodo'} / {LAYER_LABELS[selectedNode?.data?.layer] || selectedNode?.data?.layer || selectedNode?.data?.domain || 'nodo'} / {selectedNode?.data?.kind || 'feature'}</div>
          <h3>{selectedNode?.data?.title || 'Seleziona un nodo'}</h3>
          <p>{selectedNode?.data?.summary || 'Clicca un nodo per vedere cosa fa e con chi parla.'}</p>
          {selectedNode?.data?.gapStatus && selectedNode.data.gapStatus !== 'ok' && (
            <div className={`bf-gap-note bf-gap-note-${selectedNode.data.gapStatus}`}>
              {selectedNode.data.gapReason || 'Nodo da verificare rispetto al design.'}
            </div>
          )}
          {selectedNode?.data?.auditStatus && (
            <div className={`bf-audit-note bf-audit-note-${selectedNode.data.auditStatus}`}>
              <strong>{AUDIT_LABELS[selectedNode.data.auditStatus] || selectedNode.data.auditStatus}</strong>
              <span>{selectedNode.data.auditReason || 'Audit non disponibile.'}</span>
              {selectedNode.data.auditFix && <small>{selectedNode.data.auditFix}</small>}
            </div>
          )}
          {(selectedNode?.data?.uiRoute || selectedNode?.data?.apiRoute) && (
            <div className="bf-route">{selectedNode.data.httpMethod ? `${selectedNode.data.httpMethod} ` : ''}{selectedNode.data.uiRoute || selectedNode.data.apiRoute}</div>
          )}
          {selectedNode?.data?.actionDescription && (
            <div className="bf-detail-section">
              <strong>Cosa fa</strong>
              <p>{selectedNode.data.actionDescription}</p>
            </div>
          )}
          {selectedNode?.data?.subnodes?.length ? (
            <div className="bf-detail-section">
              <strong>Sotto-nodi</strong>
              <div className="bf-subnodes">
                {selectedNode.data.subnodes.slice(0, 12).map((item) => (
                  <button
                    key={item.id || item.title}
                    type="button"
                    className="bf-subnode"
                    onClick={() => openSubnode(item)}
                  >
                    <span>{item.title}</span>
                    <small>{item.description || item.route || item.kind || 'Elemento interno del nodo.'}</small>
                    {item.route && <em>{item.route}</em>}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {selectedNode?.data?.scannerEvidence && (
            <div className="bf-detail-section">
              <strong>Perche lo so</strong>
              <p>{selectedNode.data.scannerEvidence}</p>
            </div>
          )}
          <div className="bf-detail-section">
            <strong>File coinvolti</strong>
            {selectedNode?.data?.relatedFiles?.length ? (
              <ul>
                {selectedNode.data.relatedFiles.slice(0, 5).map((file) => (
                  <li key={file}><span>{file}</span></li>
                ))}
              </ul>
            ) : (
              <p className="bf-empty">Nessun file preciso collegato a questo nodo.</p>
            )}
          </div>
          <div className="bf-detail-section">
            <strong>Collegamenti visibili</strong>
            {selectedRelations.length ? (
              <ul>
                {selectedRelations.map((rel) => (
                  <li key={`${rel.source}-${rel.target}-${rel.otherTitle}`}>
                    <span>{rel.userFeedback === 'ignored' ? 'Ignorato' : rel.confidence === 'high' ? 'Certo' : 'Suggerito'}: {rel.relation || rel.label} {rel.otherTitle}</span>
                    <small>{rel.reason}{rel.evidence ? ` Evidenza: ${rel.evidence}` : ''}</small>
                    {rel.contract?.route && <small>Contratto: {rel.contract.method ? `${rel.contract.method} ` : ''}{rel.contract.route}</small>}
                    {(rel.sourceEvidence || rel.targetEvidence) && (
                      <small>Fonti: {rel.sourceEvidence || rel.sourceFiles?.[0] || rel.sourceTitle} {'->'} {rel.targetEvidence || rel.targetFiles?.[0] || rel.targetTitle}</small>
                    )}
                    <div className="bf-feedback-row">
                      <button type="button" onClick={() => sendEdgeFeedback(rel, 'confirm_edge')}>Conferma linea</button>
                      <button type="button" onClick={() => sendEdgeFeedback(rel, 'ignore_edge')}>Ignora linea</button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="bf-empty">Nessuna linea visibile per questo nodo con il filtro attuale.</p>
            )}
          </div>
          <div className="bf-detail-section">
            <strong>Prossimo passo</strong>
            <p>{selectedNode?.data?.nextAction || 'Da valutare.'}</p>
            <button type="button" onClick={copyTaskPrompt}>Trasforma in task Codex</button>
            {taskLabel && <p className="bf-empty">{taskLabel}</p>}
          </div>
          {selectedFlows.length > 0 && (
            <div className="bf-detail-section">
              <strong>Flow trace</strong>
              <ul>
                {selectedFlows.map((item) => (
                  <li key={item.id}>
                    <span>{item.status}: {item.title}</span>
                    <small>{item.chain}</small>
                    <small>{item.next_step}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {selectedPlan.length > 0 && (
            <div className="bf-detail-section">
              <strong>Piano fix</strong>
              <ul>
                {selectedPlan.map((item) => (
                  <li key={`${item.node}-${item.problem}`}>
                    <span>{item.action}</span>
                    <small>{item.check}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="bf-detail-section">
            <strong>Aiuta la skill</strong>
            <div className="bf-feedback-row">
              <button type="button" onClick={() => sendLearningFeedback('confusing')}>Non capisco</button>
              <button type="button" onClick={() => sendLearningFeedback('wrong')}>Sembra sbagliato</button>
              <button type="button" onClick={() => sendLearningFeedback('useful')}>Utile</button>
            </div>
            {feedbackLabel && <p className="bf-empty">{feedbackLabel}</p>}
          </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function mount(root) {
  createRoot(root.querySelector('[data-blueprint-flow-app]')).render(
    <ReactFlowProvider>
      <FlowBoard root={root} />
    </ReactFlowProvider>,
  );
}

document.querySelectorAll('[data-blueprint-flow-root]').forEach(mount);
