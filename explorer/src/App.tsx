import { useCallback, useEffect, useMemo, useState } from 'react';
import GraphView from './components/GraphView';
import ResourceDetails from './components/ResourceDetails';
import { loadOntology } from './rdf/ontology';
import type { DataManifest, OntologyModel } from './rdf/ontology';

function SearchIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/></svg>;
}

function filterText(text: string, query: string) {
  return text.toLowerCase().includes(query.trim().toLowerCase());
}

export default function App() {
  const [model, setModel] = useState<OntologyModel | null>(null);
  const [manifest, setManifest] = useState<DataManifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [classIri, setClassIri] = useState<string | null>(null);
  const [focus, setFocus] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [classQuery, setClassQuery] = useState('');
  const [instanceQuery, setInstanceQuery] = useState('');
  const [showTypeEdges, setShowTypeEdges] = useState(true);

  useEffect(() => {
    let cancelled = false;
    loadOntology()
      .then(({ model: loaded, manifest: info }) => {
        if (cancelled) return;
        setModel(loaded);
        setManifest(info);
        const classes = loaded.getClasses();
        // Provide a useful first view, while leaving the class selection explicit.
        const preferred = classes.find((entry) => entry.label === 'Student') ?? classes.find((entry) => entry.count > 0);
        if (preferred) setClassIri(preferred.iri);
      })
      .catch((err: unknown) => { if (!cancelled) setError(err instanceof Error ? err.message : String(err)); });
    return () => { cancelled = true; };
  }, []);

  const classes = useMemo(() => model?.getClasses() ?? [], [model]);
  const instances = useMemo(() => model && classIri ? model.getInstances(classIri) : [], [model, classIri]);
  const selectedClass = classes.find((entry) => entry.iri === classIri);
  const neighborhood = useMemo(() => model && focus ? model.getNeighborhood(focus, showTypeEdges) : null, [model, focus, showTypeEdges]);

  const navigate = useCallback((id: string) => {
    if (focus && focus !== id) setHistory((previous) => [...previous, focus]);
    setFocus(id);
  }, [focus]);

  function chooseClass(iri: string) {
    setClassIri(iri);
    setFocus(null);
    setHistory([]);
    setInstanceQuery('');
  }

  function goBack() {
    if (!history.length) return;
    const previous = history[history.length - 1];
    setHistory((current) => current.slice(0, -1));
    setFocus(previous);
  }

  if (error) return (
    <main className="status-page">
      <div className="status-icon">!</div>
      <h1>Could not load the ontology</h1>
      <p>{error}</p>
      <p className="muted">The build expects <code>../ontology/tbox.ttl</code> and <code>../ontology/abox-2025-2026.ttl</code>.</p>
    </main>
  );

  if (!model) return <main className="status-page"><div className="loader"/><h1>Loading RDF graph…</h1></main>;

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-mark"><span/><span/><span/></div>
          <div><h1>langde <span>explorer</span></h1><p>Ontology graph browser</p></div>
        </div>
        <div className="header-metadata">
          <span className="status-dot"/>
          <span>{model.size.toLocaleString()} RDF triples</span>
          <span className="header-separator">·</span>
          <span>{classes.length} classes</span>
          <a href="https://github.com/softlang/langde" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </header>
      <div className="workspace">
        <aside className="browser-panel">
          <section className="browser-section classes-section">
            <div className="section-heading"><span className="step">01</span><div><h2>Choose a class</h2><p>From the T-box</p></div></div>
            <label className="search"><SearchIcon/><input aria-label="Search classes" value={classQuery} onChange={(e) => setClassQuery(e.target.value)} placeholder="Search classes…" /></label>
            <div className="selection-list class-list">
              {classes.filter((entry) => filterText(`${entry.label} ${entry.iri}`, classQuery)).map((entry) => (
                <button key={entry.iri} title={entry.iri} className={`selection-item ${classIri === entry.iri ? 'active' : ''}`} onClick={() => chooseClass(entry.iri)}>
                  <span className="item-label">{entry.label}</span><span className="item-count">{entry.count}</span>
                </button>
              ))}
            </div>
          </section>
          <section className="browser-section instances-section">
            <div className="section-heading"><span className="step">02</span><div><h2>Choose an instance</h2><p>{selectedClass ? `${instances.length} instances of ${selectedClass.label}` : 'Select a class above'}</p></div></div>
            <label className="search"><SearchIcon/><input aria-label="Search instances" value={instanceQuery} disabled={!classIri} onChange={(e) => setInstanceQuery(e.target.value)} placeholder="Filter instances…" /></label>
            <div className="selection-list instance-list">
              {instances.filter((item) => filterText(`${item.label} ${item.id}`, instanceQuery)).map((resource) => (
                <button key={resource.id} title={resource.id} className={`selection-item ${focus === resource.id ? 'active' : ''}`} onClick={() => navigate(resource.id)}>
                  <span className="item-label">{resource.label}</span><span className="item-chevron">›</span>
                </button>
              ))}
              {instances.length === 0 ? <p className="empty-list">No asserted instances for this class.</p> : null}
            </div>
          </section>
        </aside>
        <main className="main-panel">
          <div className="graph-header">
            <div className="graph-title">
              <span className="section-kicker">03 / EXPLORE THE A-BOX</span>
              <h2>{focus ? model.label(focus) : 'Select an instance to begin'}</h2>
              <p>{neighborhood ? `${neighborhood.nodes.length} resources · ${neighborhood.edges.length} directed assertions` : 'Explore both incoming and outgoing relationships.'}</p>
            </div>
            <div className="graph-actions">
              <button className="back-button" onClick={goBack} disabled={history.length === 0} title="Navigate back">← Back</button>
              <label className="toggle"><input type="checkbox" checked={showTypeEdges} onChange={(e) => setShowTypeEdges(e.target.checked)} /><span>Show rdf:type</span></label>
            </div>
          </div>
          <div className="graph-panel">
            {focus && neighborhood ? <GraphView model={model} focus={focus} neighborhood={neighborhood} onSelect={navigate}/>
              : <div className="graph-placeholder"><div className="placeholder-glyph">◉<span>◌</span><span>◯</span></div><h3>Your graph begins here</h3><p>Select a class, then one of its instances. Click any connected resource to keep exploring.</p></div>}
          </div>
          <div className="graph-footer">
            <span><i className="legend-dot center"/> Selected resource</span>
            <span><i className="legend-dot linked"/> Connected resource</span>
            <span>Arrow direction follows RDF subject → object</span>
          </div>
        </main>
        <ResourceDetails model={model} focus={focus} neighborhood={neighborhood} />
      </div>
      <footer className="footer">
        <span>Read-only explorer · Explicit RDF assertions + named subclass membership · No OWL inference</span>
        <span title={manifest?.sources.map((item) => item.file).join(', ')}>{manifest?.sources.map((item) => item.file).join(' · ')}</span>
      </footer>
    </div>
  );
}
