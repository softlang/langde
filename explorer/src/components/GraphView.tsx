import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { Core, ElementDefinition } from 'cytoscape';
import type { Neighborhood, OntologyModel } from '../rdf/ontology';

type Props = {
  model: OntologyModel;
  focus: string;
  neighborhood: Neighborhood;
  onSelect: (id: string) => void;
};

export default function GraphView({ model, focus, neighborhood, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const graph = useRef<Core | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const elements: ElementDefinition[] = [
      ...neighborhood.nodes.map((resource) => ({
        group: 'nodes' as const,
        data: {
          id: resource.id,
          label: resource.label,
          role: resource.id === focus ? 'focus' : 'neighbor',
          subtitle: resource.types.length ? model.short(resource.types[0]) : '',
        },
      })),
      ...neighborhood.edges.map((edge, index) => ({
        group: 'edges' as const,
        data: {
          id: `edge-${index}`,
          source: edge.subject,
          target: edge.object,
          label: model.short(edge.predicate),
        },
      })),
    ];

    const cy = cytoscape({
      container: container.current,
      elements,
      minZoom: 0.08,
      maxZoom: 3.5,
      wheelSensitivity: 0.2,
      layout: {
        name: 'concentric',
        animate: false,
        fit: true,
        padding: 65,
        minNodeSpacing: 80,
        concentric: (n) => n.id() === focus ? 2 : 1,
        levelWidth: () => 1,
      },
      style: [
        {
          selector: 'node',
          style: {
            shape: 'round-rectangle',
            width: 'label',
            height: 43,
            padding: '14px',
            'background-color': '#ffffff',
            'border-width': 1.6,
            'border-color': '#a8bdd2',
            label: 'data(label)',
            color: '#25415a',
            'font-family': 'Inter, ui-sans-serif, system-ui, sans-serif',
            'font-size': 12,
            'font-weight': 500,
            'text-wrap': 'ellipsis',
            'text-max-width': '146px',
            'text-valign': 'center',
            'text-halign': 'center',
            'min-zoomed-font-size': 8,
            'overlay-opacity': 0,
          },
        },
        {
          selector: 'node[role = "focus"]',
          style: {
            'background-color': '#1a66af',
            'border-color': '#11528e',
            'border-width': 2,
            color: '#ffffff',
            'font-weight': 700,
            'font-size': 14,
          },
        },
        {
          selector: 'node:active',
          style: { 'overlay-opacity': 0.12, 'overlay-color': '#458ac8' },
        },
        {
          selector: 'edge',
          style: {
            width: 1.55,
            'line-color': '#95abc1',
            'target-arrow-color': '#7998b8',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.95,
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': 9,
            'font-family': 'Inter, ui-sans-serif, system-ui, sans-serif',
            'text-rotation': 'autorotate',
            'text-margin-y': -9,
            color: '#516b83',
            'text-background-color': '#f7fafc',
            'text-background-opacity': 0.9,
            'text-background-padding': '2px',
            'min-zoomed-font-size': 8,
          },
        },
      ],
    });

    cy.on('tap', 'node', (evt) => onSelect(evt.target.id()));
    graph.current = cy;
    return () => {
      cy.destroy();
      graph.current = null;
    };
  }, [model, focus, neighborhood, onSelect]);

  function changeZoom(factor: number) {
    const cy = graph.current;
    if (!cy) return;
    cy.zoom({
      level: Math.min(Math.max(cy.zoom() * factor, 0.08), 3.5),
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    });
  }

  return (
    <div className="graph-shell">
      <div className="graph-tools">
        <button title="Zoom in" aria-label="Zoom in" onClick={() => changeZoom(1.25)}>+</button>
        <button title="Zoom out" aria-label="Zoom out" onClick={() => changeZoom(1 / 1.25)}>−</button>
        <button className="fit" title="Fit entire neighborhood" onClick={() => graph.current?.fit(undefined, 55)}>Fit</button>
      </div>
      <div className="graph-canvas" ref={container} role="img" aria-label={`Graph of ${model.label(focus)}, with ${neighborhood.nodes.length} nodes and ${neighborhood.edges.length} directed edges. Click a node to explore it.`} />
      <div className="graph-hint">Click a node to follow a connection · Drag to pan · Scroll to zoom</div>
    </div>
  );
}
