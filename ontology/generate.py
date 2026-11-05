from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef, BNode
from rdflib.collection import Collection
from datetime import date,datetime,timedelta
from collections import Counter
from pathlib import Path
import random, json, zipfile
random.seed(202526)
D=Path(__file__).resolve().parent; ONTOLOGY_IRI='http://www.uni-koblenz.de/ontologies/langde'; EX=Namespace(ONTOLOGY_IRI+'#'); SH=Namespace('http://www.w3.org/ns/shacl#'); SKOS=Namespace('http://www.w3.org/2004/02/skos/core#')
def graph():
 g=Graph();g.bind('ld',EX);g.bind('owl',OWL);g.bind('rdfs',RDFS);g.bind('xsd',XSD);g.bind('sh',SH);g.bind('skos',SKOS);return g
T=graph();A=graph();S=graph()
def add(g,s,p,o):g.add((s,p,o))
def lit(v,dt=None,lang=None):return Literal(v,datatype=dt,lang=lang)
def klass(name,parent=None):
 c=EX[name];add(T,c,RDF.type,OWL.Class);add(T,c,RDFS.label,lit(name));
 if parent:add(T,c,RDFS.subClassOf,EX[parent]);
 return c
for n in ['Course','CourseSession','Teacher','Student','SchoolYear','GeneralSubject','SpecificSubject','School','SchoolType','GradeLevel','Language','LanguageProficiency','CEFRLevel','SchoolHolidayPeriod'] :klass(n)
klass('StandardCourse','Course');klass('PreparatoryCourse','Course')
add(T,EX.StandardCourse,OWL.disjointWith,EX.PreparatoryCourse)
def prop(name,domain,range_,datatype=False,functional=False,inverse=None):
 p=EX[name];add(T,p,RDF.type,OWL.DatatypeProperty if datatype else OWL.ObjectProperty);add(T,p,RDFS.domain,EX[domain]);add(T,p,RDFS.range,range_ if isinstance(range_,URIRef) else EX[range_]);
 if functional:add(T,p,RDF.type,OWL.FunctionalProperty)
 if inverse:add(T,p,OWL.inverseOf,EX[inverse]);
for x in [('courseId','Course',XSD.string),('label','Course',XSD.string),('firstName','Student',XSD.string),('surname','Student',XSD.string),('birthDate','Student',XSD.date),('schoolName','School',XSD.string),('gradeNumber','GradeLevel',XSD.integer),('schoolYearLabel','SchoolYear',XSD.string),('startDateTime','CourseSession',XSD.dateTime),('endDateTime','CourseSession',XSD.dateTime),('cefrRank','CEFRLevel',XSD.integer),('requiredGermanRank','Course',XSD.integer),('periodStart','SchoolHolidayPeriod',XSD.date),('periodEnd','SchoolHolidayPeriod',XSD.date)]:prop(x[0],x[1],x[2],True)
for x in [('inSchoolYear','Course','SchoolYear'),('hasDefaultTeacher','Course','Teacher'),('hasStudent','Course','Student'),('enrolledIn','Student','Course'),('hasSession','Course','CourseSession'),('sessionOf','CourseSession','Course'),('hasSubstituteTeacher','CourseSession','Teacher'),('hasGeneralSubject','Course','GeneralSubject'),('hasSpecificSubject','CourseSession','SpecificSubject'),('belongsToGeneralSubject','SpecificSubject','GeneralSubject'),('attendsSchool','Student','School'),('inGrade','Student','GradeLevel'),('hasSchoolType','School','SchoolType'),('hasNativeLanguage','Student','Language'),('hasLanguageProficiency','Student','LanguageProficiency'),('proficiencyLanguage','LanguageProficiency','Language'),('proficiencyLevel','LanguageProficiency','CEFRLevel'),('absentStudent','CourseSession','Student')]: prop(*x)
for a,b in [('hasStudent','enrolledIn'),('hasSession','sessionOf')]:add(T,EX[a],OWL.inverseOf,EX[b])
# Controlled values / nominal definitions
for cname,language in [('German','Deutsch'),('English','English'),('Arabic','العربية'),('French','français'),('Spanish','español'),('Turkish','Türkçe'),('Ukrainian','українська'),('Russian','русский'),('Polish','polski'),('Romanian','română'),('Persian','فارسی'),('Kurdish','Kurdî'),('Italian','italiano'),('Portuguese','português'),('Albanian','shqip'),('Vietnamese','Tiếng Việt'),('Bosnian','bosanski'),('Serbian','srpski'),('Dari','دری')]:
 add(A,EX[cname],RDF.type,EX.Language);add(A,EX[cname],RDFS.label,lit(language))
for i,l in enumerate(['A1','A2','B1','B2','C1','C2'],1):
 add(A,EX['CEFR_'+l],RDF.type,EX.CEFRLevel);add(A,EX['CEFR_'+l],RDFS.label,lit(l));add(A,EX['CEFR_'+l],EX.cefrRank,lit(i,XSD.integer))
for n,label in [('Gymnasium','Gymnasium'),('RealschulePlus','Realschule plus'),('VocationalSchool','Berufsbildende Schule'),('ComprehensiveSchool','Integrierte Gesamtschule')]:add(A,EX[n],RDF.type,EX.SchoolType);add(A,EX[n],RDFS.label,lit(label))
for n in range(9,14):add(A,EX[f'Grade{n}'],RDF.type,EX.GradeLevel);add(A,EX[f'Grade{n}'],EX.gradeNumber,lit(n,XSD.integer))
sy=EX.SY2025_2026;add(A,sy,RDF.type,EX.SchoolYear);add(A,sy,EX.schoolYearLabel,lit('2025/2026'))
subjects={
 'Mathematics':['Differentiation','GaussianElimination','LinearFunctions','Probability','Equations','Geometry'],
 'Biology':['Evolution','Reproduction','CellBiology','Genetics','Ecosystems'],
 'Geography':['ClimateZones','RiverSystems','Urbanization','Migration'],
 'History':['Industrialization','WeimarRepublic','EuropeanIntegration','Democracy'],
 'Physics':['ElectricCircuits','Motion','EnergyConservation','Optics'],
 'GermanLanguage':['Grammar','ReadingComprehension','ConversationalGerman','AcademicVocabulary','WritingSkills'],
 'Chemistry':['ChemicalReactions','AcidsAndBases','PeriodicTable']}
for gen,topics in subjects.items():
 add(A,EX[gen],RDF.type,EX.GeneralSubject);add(A,EX[gen],RDFS.label,lit(gen.replace('GermanLanguage','German language')))
 for top in topics:
  add(A,EX[top],RDF.type,EX.SpecificSubject);add(A,EX[top],RDFS.label,lit(top));add(A,EX[top],EX.belongsToGeneralSubject,EX[gen])
# Holiday dates official ministry + modeled optional common movable holidays from illustrative calendar
holidays=[('AutumnBreak',date(2025,10,13),date(2025,10,24)),('ChristmasBreak',date(2025,12,22),date(2026,1,7)),('EasterBreak',date(2026,3,30),date(2026,4,10)),('SummerBreak2026',date(2026,6,29),date(2026,8,7))]
for label,a,b in holidays:
 h=EX[label];add(A,h,RDF.type,EX.SchoolHolidayPeriod);add(A,h,EX.periodStart,lit(a.isoformat(),XSD.date));add(A,h,EX.periodEnd,lit(b.isoformat(),XSD.date))
# Conservatively avoid common movable-holiday dates, though local schools have distinct calendars.
extra_days={date.fromisoformat(s) for s in ['2025-10-03','2025-11-01','2025-12-25','2025-12-26','2026-01-01','2026-04-03','2026-04-06','2026-05-01','2026-05-14','2026-05-25','2026-06-04','2026-02-12','2026-02-13','2026-02-16','2026-02-17','2026-02-18','2026-05-15','2026-06-05']}
def valid(d):return d.weekday()<5 and d not in extra_days and all(not a<=d<=b for _,a,b in holidays) and date(2025,8,18)<=d<=date(2026,6,26)
schools=[('ElmbachGymnasium','Elmbach-Gymnasium','Gymnasium'),('WaldbrueckenRealschule','Waldbrücken-Realschule plus','RealschulePlus'),('FalkenhofBBS','Berufsbildende Schule Falkenhof','VocationalSchool'),('LindenquellIGS','Integrierte Gesamtschule Lindenquell','ComprehensiveSchool'),('NordtalGymnasium','Nordtal-Gymnasium','Gymnasium'),('SteinwieseBBS','Berufsbildende Schule Steinwiese','VocationalSchool')]
for s,label,t in schools:
 add(A,EX[s],RDF.type,EX.School);add(A,EX[s],EX.schoolName,lit(label));add(A,EX[s],EX.hasSchoolType,EX[t])
teachers=[('Mara','Seifert'),('Jonas','Winter'),('Elena','Voss'),('David','Hartwig'),('Sofia','Bergmann'),('Leonie','Falk'),('Nils','Kramer'),('Aylin','Neumann'),('Robin','Keller'),('Tessa','Brandt'),('Noah','Reiter'),('Iris','Sommer')]
for i,(f,l) in enumerate(teachers,1):
 t=EX[f'Teacher{i:02}'];add(A,t,RDF.type,EX.Teacher);add(A,t,RDFS.label,lit(f+' '+l))
# Course 5 and 9 preparatory, rest standard; exactly one mixed general-subject course
courses=[('Standard','Mathematics',28,6,0,0,0),('Standard','Biology',26,5,1,1,1),('Standard','Geography',14,4,2,2,2),('Standard','Mathematics',29,7,3,3,3),('Preparatory','GermanLanguage',25,5,4,4,4),('Standard','History',27,6,0,0,5),('Standard','Physics',13,3,1,1,6),('Standard','Chemistry',24,5,2,2,7),('Preparatory','Mathematics',18,4,3,3,8),('Standard','Mathematics+Biology',28,6,4,4,9)]
# course tuple: type, subjects, sessions, students, weekday Mon..Fri, hour offset, teacher index
firsts=['Amira','Yara','Dilan','Leyla','Omar','Rania','Mila','Farid','Sara','Nadia','Khalil','Ana','Tarek','Emina','Ibrahim','Elif','Petro','Lina','Azra','Boris','Meryem','Noor','Selin','Marta','Nour','Elias','Iryna','Samir','Daria','Hana','Adnan','Yusuf','Alina','Rami','Rasha','Zara','Maksym','Leila','Nika','Kaan','Maya','Iman','Mina','Tarik','Mariam','Amina','Luka','Murat','Fatima','Lara','Emir','Alma','Yasmin','Nikolai']
lasts=['Karimi','Demir','Haddad','Nowak','Jovic','Kaya','Hassan','Pavlenko','Rahmani','Aslan','Petrov','Yilmaz','Tomic','Faris','Mansour','Dervishi','Ionescu','Ahmed','Kovalenko','Sahin','Dabiri','Rossi','Kowalska','Dogan','Hoxha','Saleh','Markovic','Ismail','Radovic','Bashir','Popescu','Yousef','Nouri','Stojanov','Mustafa','Osman','Baran','Najjar','Dragic','Abadi','Sokolov','Hamdan','Celik','Moradi','Ali','Sami','Mirza','Miftari','Radu','Kazemi','Arslan','Sharif','Lazic','Avdi']
native=['Arabic','Turkish','Ukrainian','Russian','Polish','Romanian','Persian','Kurdish','Albanian','Bosnian','Serbian','Dari','French','Spanish','Vietnamese','Italian','Portuguese']
source_languages=['English','French','Spanish','Turkish','Arabic','Russian','Ukrainian','Polish','Italian']
cefr=['A1','A2','B1','B2','C1','C2']
student_index=0;session_total=0;absence_total=0;sub_count=0
for ci,(ctype,general,n_sessions,n_students,weekday,hour_i,teacher_i) in enumerate(courses,1):
 course=EX[f'Course{ci:02}'];add(A,course,RDF.type,EX[ctype+'Course']);add(A,course,EX.courseId,lit(f'C{ci:02}'));add(A,course,EX.label,lit(f'{ctype} course {ci:02}'));add(A,course,EX.inSchoolYear,sy);add(A,course,EX.hasDefaultTeacher,EX[f'Teacher{teacher_i+1:02}']);add(A,course,EX.requiredGermanRank,lit(3 if ctype=='Standard' else 2,XSD.integer))
 gens=general.split('+')
 for gen in gens:add(A,course,EX.hasGeneralSubject,EX[gen])
 enrolled=[]
 for si in range(n_students):
  student_index+=1;sid=EX[f'Student{student_index:03}'];enrolled.append(sid)
  add(A,sid,RDF.type,EX.Student);add(A,sid,EX.firstName,lit(firsts[(student_index-1)%len(firsts)]));add(A,sid,EX.surname,lit(lasts[(student_index*7)%len(lasts)]))
  grade=9+(student_index+ci)%5
  # almost all ages are grade-consistent; range 14..21
  age=max(14,min(21,grade+5+random.choice([-1,0,0,1,2])))
  birthyear=2025-age
  dob=date(birthyear,random.randint(1,12),random.randint(1,28))
  add(A,sid,EX.birthDate,lit(dob.isoformat(),XSD.date))
  school=schools[(student_index+ci)%len(schools)][0];add(A,sid,EX.attendsSchool,EX[school]);add(A,sid,EX.inGrade,EX[f'Grade{grade}'])
  add(A,course,EX.hasStudent,sid);add(A,sid,EX.enrolledIn,course)
  l1=native[(student_index*3+ci)%len(native)];add(A,sid,EX.hasNativeLanguage,EX[l1])
  if student_index%8==0:
   l2=native[(student_index*3+ci+5)%len(native)]
   if l2!=l1:add(A,sid,EX.hasNativeLanguage,EX[l2])
  ger_level=random.choice(['A2','A2','A1']) if ctype=='Preparatory' else random.choice(['B1','B1','B2','C1'])
  def proficiency(lang,lv):
   p=EX[f'Proficiency{student_index:03}_{lang}'];add(A,p,RDF.type,EX.LanguageProficiency);add(A,sid,EX.hasLanguageProficiency,p);add(A,p,EX.proficiencyLanguage,EX[lang]);add(A,p,EX.proficiencyLevel,EX['CEFR_'+lv])
  proficiency('German',ger_level)
  extra=source_languages[(student_index+ci)%len(source_languages)]
  if extra=='German':extra='English'
  if extra!=l1:proficiency(extra,random.choice(['A1','A2','B1','B2','C1']))
  if student_index%5==0:
   extra2='English' if extra!='English' and l1!='English' else 'French'
   if extra2!=extra and extra2!=l1:proficiency(extra2,random.choice(['A2','B1','B2']))
 # generate weekday anchors + session selection. A biweekly-like course uses every other week.
 all_days=[date(2025,8,18)+timedelta(days=n) for n in range((date(2026,6,26)-date(2025,8,18)).days+1)]
 possibilities=[d for d in all_days if d.weekday()==weekday and valid(d)]
 if n_sessions<=18:
  preferred=possibilities[::2]
  if len(preferred)<n_sessions:preferred=possibilities[1::2]
  chosen=preferred[:n_sessions] if len(preferred)>=n_sessions else possibilities[:n_sessions]
 else:
  chosen=possibilities[:n_sessions]
 assert len(chosen)==n_sessions,(ci,len(possibilities),n_sessions)
 for sess_idx,d in enumerate(chosen,1):
  ses=EX[f'Session{ci:02}_{sess_idx:02}'];add(A,ses,RDF.type,EX.CourseSession);add(A,course,EX.hasSession,ses);add(A,ses,EX.sessionOf,course)
  hour=15+(ci%3);st=datetime(d.year,d.month,d.day,hour,0);en=st+timedelta(minutes=90)
  add(A,ses,EX.startDateTime,lit(st.isoformat(timespec='seconds'),XSD.dateTime));add(A,ses,EX.endDateTime,lit(en.isoformat(timespec='seconds'),XSD.dateTime))
  gen=gens[(sess_idx-1)%len(gens)];topics=subjects[gen];topic=topics[(sess_idx-1)%len(topics)];add(A,ses,EX.hasSpecificSubject,EX[topic])
  if len(gens)>1 and sess_idx%5==0:
   other=gens[(sess_idx)%len(gens)];add(A,ses,EX.hasSpecificSubject,EX[subjects[other][(sess_idx//5)%len(subjects[other])]])
  if sess_idx%13==0:
   sub=EX[f'Teacher{11+(sess_idx%2):02}'];add(A,ses,EX.hasSubstituteTeacher,sub);sub_count+=1
  if (ci*37+sess_idx*11)%10==0: # occasional absences
   missing=random.choice(enrolled);add(A,ses,EX.absentStudent,missing);absence_total+=1
  elif sess_idx%17==0:
   missing=random.choice(enrolled);add(A,ses,EX.absentStudent,missing);absence_total+=1
  session_total+=1
# Ontology metadata, semantics
ontology=URIRef(ONTOLOGY_IRI);add(T,ontology,RDF.type,OWL.Ontology);add(T,ontology,RDFS.label,lit('langde'));add(T,ontology,RDFS.comment,lit('An experiment with a particular German language school design as a synthesized variation on https://wp.uni-koblenz.de/funkprojekt/'));add(T,ontology,RDFS.comment,lit('OWL vocabulary for fictional German-support courses. Admission, scheduling, and cross-resource integrity rules are validated with SHACL.'))
# A-Box ontology header and imports
abox=EX['synthetic-2025-2026'];add(A,abox,RDF.type,OWL.Ontology);add(A,abox,OWL.imports,ontology)
# OWL class restrictions (minimums and German exclusion); no arbitrary closed-world completion asserted.
def restriction(propname,minn=None,exact=None,hasvalue=None):
 b=BNode();add(T,b,RDF.type,OWL.Restriction);add(T,b,OWL.onProperty,EX[propname]);
 if minn is not None:add(T,b,OWL.minCardinality,lit(minn,XSD.nonNegativeInteger))
 if exact is not None:add(T,b,OWL.cardinality,lit(exact,XSD.nonNegativeInteger))
 if hasvalue is not None:add(T,b,OWL.hasValue,hasvalue)
 return b
for cl,pr,n in [('Student','hasNativeLanguage',1),('Course','hasGeneralSubject',1),('CourseSession','hasSpecificSubject',1)]:add(T,EX[cl],RDFS.subClassOf,restriction(pr,minn=n))
for cl,pr in [('Course','hasDefaultTeacher'),('Course','inSchoolYear'),('CourseSession','sessionOf'),('Student','attendsSchool'),('Student','inGrade'),('School','hasSchoolType'),('LanguageProficiency','proficiencyLanguage'),('LanguageProficiency','proficiencyLevel')]:add(T,EX[cl],RDFS.subClassOf,restriction(pr,exact=1))
no_german=BNode();add(T,no_german,RDF.type,OWL.Class);not_sub=BNode();add(T,not_sub,RDF.type,OWL.Restriction);add(T,not_sub,OWL.onProperty,EX.hasNativeLanguage);add(T,not_sub,OWL.hasValue,EX.German);add(T,no_german,OWL.complementOf,not_sub);add(T,EX.Student,RDFS.subClassOf,no_german)
# SHACL helpers: explicit shapes and SPARQL constraint via sh:sparql
prefixes='PREFIX ld: <http://www.uni-koblenz.de/ontologies/langde#>\nPREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n'
def shape(name,target):
 s=EX[name];add(S,s,RDF.type,SH.NodeShape);add(S,s,SH.targetClass,EX[target]);return s
def pshape(s,path,minc=None,maxc=None,kind=None,datatype=None,cls=None,pattern=None):
 b=BNode();add(S,s,SH.property,b);add(S,b,SH.path,EX[path]);
 if minc is not None:add(S,b,SH.minCount,lit(minc,XSD.integer))
 if maxc is not None:add(S,b,SH.maxCount,lit(maxc,XSD.integer))
 if datatype:add(S,b,SH.datatype,datatype)
 if cls:add(S,b,SH['class'],EX[cls])
 if pattern:add(S,b,SH.pattern,lit(pattern))
 return b
def sparql(s,msg,query):
 b=BNode();add(S,s,SH.sparql,b);add(S,b,SH.message,lit(msg));add(S,b,SH.select,lit(prefixes+query))
cs=shape('CourseShape','Course')
add(S,cs,SH.targetClass,EX.StandardCourse)
add(S,cs,SH.targetClass,EX.PreparatoryCourse)
for k,mi,ma,dt,cl in [('courseId',1,1,XSD.string,None),('label',1,1,XSD.string,None),('inSchoolYear',1,1,None,'SchoolYear'),('hasDefaultTeacher',1,1,None,'Teacher'),('hasGeneralSubject',1,None,None,'GeneralSubject'),('hasStudent',3,7,None,'Student'),('requiredGermanRank',1,1,XSD.integer,None)]:pshape(cs,k,mi,ma,datatype=dt,cls=cl)
sparql(cs,'Student German CEFR rank is lower than the course admission threshold.', '''SELECT $this ?student WHERE { $this ld:hasStudent ?student ; ld:requiredGermanRank ?required . ?student ld:hasLanguageProficiency ?p . ?p ld:proficiencyLanguage ld:German ; ld:proficiencyLevel/ld:cefrRank ?rank . FILTER (?rank < ?required) }''')
# Avoid a nested SELECT: SHACL-SPARQL potentially pre-bound variables (notably
# $this) cannot be referenced only outside a subquery. Two EXISTS tests express
# the exact-one rule without aggregation or correlated subqueries.
sparql(cs,'Course student must have exactly one German CEFR record.', '''SELECT $this ?student WHERE {
  $this ld:hasStudent ?student .
  FILTER (
    NOT EXISTS {
      ?student ld:hasLanguageProficiency ?p .
      ?p ld:proficiencyLanguage ld:German .
    }
    ||
    EXISTS {
      ?student ld:hasLanguageProficiency ?p1, ?p2 .
      ?p1 ld:proficiencyLanguage ld:German .
      ?p2 ld:proficiencyLanguage ld:German .
      FILTER (?p1 != ?p2)
    }
  )
}''')
ss=shape('SessionShape','CourseSession')
for k,mi,ma,dt,cl in [('sessionOf',1,1,None,'Course'),('startDateTime',1,1,XSD.dateTime,None),('endDateTime',1,1,XSD.dateTime,None),('hasSpecificSubject',1,None,None,'SpecificSubject'),('hasSubstituteTeacher',0,1,None,'Teacher'),('absentStudent',0,None,None,'Student')]:pshape(ss,k,mi,ma,datatype=dt,cls=cl)
sparql(ss,'Session topic must be covered by one of the course general subjects.', '''SELECT $this ?topic WHERE { $this ld:sessionOf ?course ; ld:hasSpecificSubject ?topic . FILTER NOT EXISTS { ?topic ld:belongsToGeneralSubject ?general . ?course ld:hasGeneralSubject ?general } }''')
sparql(ss,'Absent student must be enrolled in the session course.', '''SELECT $this ?student WHERE { $this ld:absentStudent ?student ; ld:sessionOf ?course . FILTER NOT EXISTS { ?course ld:hasStudent ?student } }''')
sparql(ss,'Substitute teacher cannot be the default course teacher.', '''SELECT $this ?sub WHERE { $this ld:hasSubstituteTeacher ?sub ; ld:sessionOf/ld:hasDefaultTeacher ?sub . }''')
sparql(ss,'Session must start before it ends.', '''SELECT $this WHERE { $this ld:startDateTime ?start ; ld:endDateTime ?end . FILTER (?start >= ?end) }''')
sparql(ss,'Session date must fall outside encoded school holidays.', '''SELECT $this ?holiday WHERE { $this ld:startDateTime ?start . ?holiday a ld:SchoolHolidayPeriod ; ld:periodStart ?a ; ld:periodEnd ?b . FILTER (SUBSTR(STR(?start),1,10) >= STR(?a) && SUBSTR(STR(?start),1,10) <= STR(?b)) }''')
stu=shape('StudentShape','Student')
for k,mi,ma,dt,cl in [('firstName',1,1,XSD.string,None),('surname',1,1,XSD.string,None),('birthDate',1,1,XSD.date,None),('attendsSchool',1,1,None,'School'),('inGrade',1,1,None,'GradeLevel'),('hasNativeLanguage',1,None,None,'Language'),('enrolledIn',1,1,None,'Course'),('hasLanguageProficiency',1,None,None,'LanguageProficiency')]:pshape(stu,k,mi,ma,datatype=dt,cls=cl)
sparql(stu,'German must not be a student native language.', '''SELECT $this WHERE { $this ld:hasNativeLanguage ld:German . }''')
sparql(stu,'Student must be linked to the same course in both directions.', '''SELECT $this ?course WHERE { $this ld:enrolledIn ?course . FILTER NOT EXISTS { ?course ld:hasStudent $this } }''')
sparql(stu,'Student must be between 11 and 21 years old at school-year start (2025-08-18).', '''SELECT $this WHERE { $this ld:birthDate ?dob . BIND((2025 - YEAR(?dob) - IF(MONTH(?dob) > 8 || (MONTH(?dob) = 8 && DAY(?dob) > 18), 1, 0)) AS ?age) FILTER (?age < 11 || ?age > 21) }''')
ps=shape('ProficiencyShape','LanguageProficiency');pshape(ps,'proficiencyLanguage',1,1,cls='Language');pshape(ps,'proficiencyLevel',1,1,cls='CEFRLevel')
sc=shape('SchoolShape','School');pshape(sc,'schoolName',1,1,datatype=XSD.string);pshape(sc,'hasSchoolType',1,1,cls='SchoolType')
sp=shape('SpecificSubjectShape','SpecificSubject');pshape(sp,'belongsToGeneralSubject',1,None,cls='GeneralSubject')
for name,g in [('tbox.ttl',T),('abox-2025-2026.ttl',A),('shapes.ttl',S)]:g.serialize(destination=str(D/name),format='turtle')
summary={'courses':len(courses),'standard_courses':8,'preparatory_courses':2,'sessions':session_total,'students':student_index,'teachers':len(teachers),'schools':len(schools),'absence_records':absence_total,'substitute_sessions':sub_count,'triples':{'tbox':len(T),'abox':len(A),'shapes':len(S)},'course_session_counts':[x[2] for x in courses],'course_student_counts':[x[3] for x in courses]}
(D/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
# data-level integrity check over source graphs
assert sum(1 for _ in A.subjects(RDF.type,EX.CourseSession))==session_total
for ses in A.subjects(RDF.type,EX.CourseSession):
 st=str(A.value(ses,EX.startDateTime))[:10];assert valid(date.fromisoformat(st)),st
 co=A.value(ses,EX.sessionOf)
 for top in A.objects(ses,EX.hasSpecificSubject):assert any((top,EX.belongsToGeneralSubject,g) in A for g in A.objects(co,EX.hasGeneralSubject))
 for absent in A.objects(ses,EX.absentStudent):assert (co,EX.hasStudent,absent) in A
for student in A.subjects(RDF.type,EX.Student):assert (student,EX.hasNativeLanguage,EX.German) not in A
README=f'''# langde — synthetic course ontology (school year 2025/2026)\n\nAn experiment with a particular German language school design as a synthesized variation on https://wp.uni-koblenz.de/funkprojekt/\n\nFiles: `tbox.ttl` (OWL vocabulary), `abox-2025-2026.ttl` (fictional individuals), `shapes.ttl` (SHACL), `summary.json` (metrics), `Makefile` (validation), `requirements.txt` (Python dependencies), `generate.py` (reproducible generation), `smoke_shacl_sparql.py` (SPARQL regression checks).\n\nOntology IRI: `http://www.uni-koblenz.de/ontologies/langde`\nPrefix: `ld:` = `http://www.uni-koblenz.de/ontologies/langde#`.\n\n## SHACL validation
Run `make install` once to install dependencies, then `make validate` to validate the A-Box with the T-Box and SHACL shapes. `make smoke` checks the SHACL-SPARQL queries using RDFLib (including negative regression cases) without running the full SHACL engine. `make check` runs both smoke checks and pySHACL validation. `make regenerate` recreates the Turtle files from `generate.py` (and the summary/README).

## Dataset\n- {summary['courses']} courses (8 standard, 2 preparatory); {session_total} sessions, {student_index} students, {len(teachers)} teachers, {len(schools)} entirely fictional schools.\n- {absence_total} session-absence assertions and {sub_count} substitute-session assertions.\n- Student ages at school-year start are within 11–21, mostly age-appropriate for grades 9–13.\n- German CEFR ranks: A1=1, A2=2, B1=3, B2=4, C1=5, C2=6. Standard courses require rank >=3 (B1); preparatory courses require rank >=2 (A2) as an explicit **synthetic assumption**: the user's lower cutoff for preparatory courses was not settled, so generated A1 examples are excluded by the chosen local threshold.\n- Two or more general subjects on Course10, with session topics from the permitted subject areas.\n- Every synthetic student attends exactly one course. Student school/grade affiliation is modeled directly.\n\n## Calendaring\n- Session dates are between 2025-08-18 and 2026-06-26, Monday–Friday, avoiding official RLP autumn (2025-10-13–24), Christmas (2025-12-22–2026-01-07), Easter (2026-03-30–04-10), and 2026 summer (from 2026-06-29) holidays, and state public holidays.\n- Also conservatively avoid representative Carnival/bridge-day dates (2026-02-12–18, 2026-05-15, 2026-06-05). These are NOT uniform state-wide school holidays; each school has its own movable days. The dataset does not assert that each fictional school uses an official school-specific calendar.\n- Sources: https://bm.rlp.de/service/ferientermine/seite ; https://mdi.rlp.de/themen/buerger-und-staat/verfassung-und-verwaltung/sonn-und-feiertagsrecht\n\n## Semantics and validation\n- OWL intentionally uses open-world semantics. For closed-world completeness, numerical ranges, cross-property consistency, holiday exclusion, and admission checks, use SHACL.\n- SHACL SPARQL checks require a SHACL engine implementing SPARQL constraints.\n- Native-language German exclusion is expressed in both OWL and SHACL.\n- Explicit `enrolledIn` and `hasStudent` / `sessionOf` and `hasSession` are mutually inverse.\n- `requiredGermanRank` is a course-level *test data rule*, and the preparatory A2 threshold is provisional.\n- Session scheduling is synthetic; rooms, timetable clashes, student consent and personally identifiable real records are deliberately absent.\n'''
(D/'README.md').write_text(README,encoding='utf8')
with zipfile.ZipFile(str(D.parent/'langde-2025-2026.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for f in D.iterdir():
  if f.is_file():z.write(f,arcname=f.name)
print(json.dumps(summary,indent=2))
