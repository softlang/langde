import type { Neighborhood, OntologyModel } from '../rdf/ontology';

type Props = {
  model: OntologyModel;
  focus: string | null;
  neighborhood: Neighborhood | null;
  open: boolean;
  onClose: () => void;
};

export default function ResourceDetails({ model, focus, neighborhood, open, onClose }: Props) {
  const panelClassName = `details-panel ${open ? 'open' : ''}`;
  const closeButton = <button className="details-close" type="button" onClick={onClose} aria-label="Close details">×</button>;
  if (!focus || !neighborhood) {
    return <aside id="resource-details" className={panelClassName}>{closeButton}<h2>Resource details</h2><p className="muted">Select an instance to see its properties.</p></aside>;
  }
  const resource = model.resource(focus);
  return (
    <aside id="resource-details" className={panelClassName}>
      {closeButton}
      <div className="section-kicker">CURRENT RESOURCE</div>
      <h2 className="details-title">{resource.label}</h2>
      <div className="type-list">
        {resource.types.length
          ? resource.types.map((type) => <span className="type-pill" title={type} key={type}>{model.short(type)}</span>)
          : <span className="type-pill muted">No asserted type</span>}
      </div>
      <h3>IRI</h3>
      <div className="iri-box">{focus}</div>
      <button className="copy-button" onClick={() => navigator.clipboard?.writeText(focus)}>Copy IRI</button>
      <h3>Connections</h3>
      <div className="counts-row">
        <div><strong>{neighborhood.incoming}</strong><small>Incoming</small></div>
        <div><strong>{neighborhood.outgoing}</strong><small>Outgoing</small></div>
      </div>
      <h3>Literal properties <span className="muted">({neighborhood.literals.length})</span></h3>
      {neighborhood.literals.length === 0 ? <p className="muted">No literal assertions on this resource.</p> :
        <dl className="literal-list">
          {neighborhood.literals.map((property, index) => (
            <div key={`${property.predicate}-${index}`}>
              <dt title={property.predicate}>{model.short(property.predicate)}</dt>
              <dd>{property.value}{property.language ? <small> @{property.language}</small> : null}</dd>
            </div>
          ))}
        </dl>}
    </aside>
  );
}
