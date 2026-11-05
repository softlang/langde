import { DataFactory, Parser, Store } from 'n3';
import type { Quad, Term } from '@rdfjs/types';

export const NS = {
  rdfType: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
  rdfsLabel: 'http://www.w3.org/2000/01/rdf-schema#label',
  rdfsClass: 'http://www.w3.org/2000/01/rdf-schema#Class',
  rdfsSubClassOf: 'http://www.w3.org/2000/01/rdf-schema#subClassOf',
  owlClass: 'http://www.w3.org/2002/07/owl#Class',
  langde: 'http://www.uni-koblenz.de/ontologies/langde#',
};

export type RdfClass = { iri: string; label: string; count: number };
export type RdfResource = { id: string; label: string; types: string[] };
export type ResourceEdge = { subject: string; predicate: string; object: string };
export type LiteralProperty = { predicate: string; value: string; language?: string; datatype?: string };
export type Neighborhood = {
  nodes: RdfResource[];
  edges: ResourceEdge[];
  incoming: number;
  outgoing: number;
  literals: LiteralProperty[];
};

function resourceId(term: Term): string | null {
  if (term.termType === 'NamedNode') return term.value;
  if (term.termType === 'BlankNode') return `_:${term.value}`;
  return null;
}

function node(id: string) {
  return id.startsWith('_:') ? DataFactory.blankNode(id.slice(2)) : DataFactory.namedNode(id);
}

function localName(iri: string): string {
  if (iri.startsWith('_:')) return `Blank node ${iri.slice(2, 10)}`;
  const end = iri.split(/[\/#]/).filter(Boolean).pop() || iri;
  try { return decodeURIComponent(end); } catch { return end; }
}

function compareLabels(a: RdfResource, b: RdfResource): number {
  return a.label.localeCompare(b.label, undefined, { numeric: true, sensitivity: 'base' });
}

/** An asserted RDF graph, with lightweight RDFS subclass traversal (no OWL reasoning). */
export class OntologyModel {
  private readonly store: Store;
  readonly size: number;

  constructor(text: string) {
    const parser = new Parser({ format: 'N-Triples' });
    const quads = parser.parse(text);
    this.store = new Store(quads);
    this.size = this.store.size;
  }

  private quads(subject: string | null, predicate: string | null, object: string | null): Quad[] {
    return this.store.getQuads(
      subject === null ? null : node(subject),
      predicate === null ? null : DataFactory.namedNode(predicate),
      object === null ? null : node(object),
      null,
    );
  }

  private firstLiteral(subject: string, predicate: string): string | undefined {
    return this.quads(subject, predicate, null)
      .find((quad) => quad.object.termType === 'Literal')?.object.value;
  }

  label(id: string): string {
    const rdfLabel = this.firstLiteral(id, NS.rdfsLabel);
    if (rdfLabel) return rdfLabel;
    const domainLabel = this.firstLiteral(id, `${NS.langde}label`);
    if (domainLabel) return domainLabel;
    const first = this.firstLiteral(id, `${NS.langde}firstName`);
    const last = this.firstLiteral(id, `${NS.langde}surname`);
    if (first || last) return [first, last].filter(Boolean).join(' ');
    const schoolName = this.firstLiteral(id, `${NS.langde}schoolName`);
    if (schoolName) return schoolName;
    return localName(id);
  }

  short(iri: string): string {
    if (iri.startsWith(NS.langde)) return `ld:${iri.slice(NS.langde.length)}`;
    if (iri.startsWith('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
      return `rdf:${iri.split('#').pop()}`;
    if (iri.startsWith('http://www.w3.org/2000/01/rdf-schema#'))
      return `rdfs:${iri.split('#').pop()}`;
    if (iri.startsWith('http://www.w3.org/2002/07/owl#'))
      return `owl:${iri.split('#').pop()}`;
    return localName(iri);
  }

  types(id: string): string[] {
    return [...new Set(this.quads(id, NS.rdfType, null)
      .map((quad) => resourceId(quad.object))
      .filter((value): value is string => Boolean(value)))];
  }

  resource(id: string): RdfResource {
    return { id, label: this.label(id), types: this.types(id) };
  }

  /** Named OWL/RDFS classes declared in the T-box. */
  classIris(): string[] {
    const iriSet = new Set<string>();
    for (const classType of [NS.owlClass, NS.rdfsClass]) {
      for (const quad of this.quads(null, NS.rdfType, classType)) {
        if (quad.subject.termType === 'NamedNode') iriSet.add(quad.subject.value);
      }
    }
    return [...iriSet];
  }

  /** Named subclasses, including the class itself, transitively. */
  subclassesOf(classIri: string): string[] {
    const known = new Set(this.classIris());
    const visited = new Set([classIri]);
    const queue = [classIri];
    while (queue.length > 0) {
      const current = queue.shift()!;
      for (const quad of this.quads(null, NS.rdfsSubClassOf, current)) {
        const child = resourceId(quad.subject);
        if (!child || !known.has(child) || visited.has(child)) continue;
        visited.add(child);
        queue.push(child);
      }
    }
    return [...visited];
  }

  getInstances(classIri: string): RdfResource[] {
    const ids = new Set<string>();
    for (const subclass of this.subclassesOf(classIri)) {
      for (const quad of this.quads(null, NS.rdfType, subclass)) {
        const id = resourceId(quad.subject);
        if (id) ids.add(id);
      }
    }
    return [...ids].map((id) => this.resource(id)).sort(compareLabels);
  }

  getClasses(): RdfClass[] {
    return this.classIris()
      .map((iri) => ({ iri, label: this.label(iri), count: this.getInstances(iri).length }))
      .sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' }));
  }

  getNeighborhood(focus: string, showTypeEdges = true): Neighborhood {
    const outgoingQuads = this.quads(focus, null, null);
    const incomingQuads = this.quads(null, null, focus);
    const edgeMap = new Map<string, ResourceEdge>();
    const nodeIds = new Set([focus]);

    for (const quad of [...outgoingQuads, ...incomingQuads]) {
      if (!showTypeEdges && quad.predicate.value === NS.rdfType) continue;
      const s = resourceId(quad.subject);
      const o = resourceId(quad.object);
      if (!s || !o) continue;
      const edge = { subject: s, predicate: quad.predicate.value, object: o };
      edgeMap.set(JSON.stringify([s, edge.predicate, o]), edge);
      nodeIds.add(s);
      nodeIds.add(o);
    }

    const literals: LiteralProperty[] = outgoingQuads
      .flatMap((quad) => {
        const value = quad.object;
        if (value.termType !== 'Literal') return [];
        return [{
          predicate: quad.predicate.value,
          value: value.value,
          language: value.language || undefined,
          datatype: value.datatype.value,
        }];
      })
      .sort((a, b) => this.short(a.predicate).localeCompare(this.short(b.predicate)));

    const edges = [...edgeMap.values()].sort((a, b) =>
      a.predicate.localeCompare(b.predicate) || a.subject.localeCompare(b.subject) || a.object.localeCompare(b.object));
    return {
      nodes: [...nodeIds].map((id) => this.resource(id)).sort(compareLabels),
      edges,
      incoming: edges.filter((edge) => edge.object === focus).length,
      outgoing: edges.filter((edge) => edge.subject === focus).length,
      literals,
    };
  }
}

export type DataManifest = {
  triples: number;
  sources: { file: string; format: string; triples: number }[];
  format: string;
};

export async function loadOntology(): Promise<{ model: OntologyModel; manifest: DataManifest }> {
  const path = `${import.meta.env.BASE_URL}data/`;
  const [manifestResponse, dataResponse] = await Promise.all([
    fetch(`${path}manifest.json`),
    fetch(`${path}ontology.nt`),
  ]);
  if (!manifestResponse.ok || !dataResponse.ok) {
    throw new Error('Ontology data is missing. Run "npm run prepare:data" from explorer/ and reload.');
  }
  const [manifest, data] = await Promise.all([
    manifestResponse.json() as Promise<DataManifest>,
    dataResponse.text(),
  ]);
  return { model: new OntologyModel(data), manifest };
}
