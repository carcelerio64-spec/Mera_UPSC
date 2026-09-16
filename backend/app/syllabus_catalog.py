"""UPSC CSE syllabus navigation catalog with fail-closed topic helpers.

The app keeps concise Hindi navigation labels here. Official notification remains the source of truth;
Optional detail is served by optional_syllabus_registry and is not marked complete until verified.
"""
from .upsc_cse_structure import ALL_OPTIONALS,OFFICIAL_NOTIFICATION_SOURCE
PRELIMS=[
{"paper":"GS Paper-I","subject":"Current Affairs","topics":["राष्ट्रीय और अंतरराष्ट्रीय महत्व की समसामयिक घटनाएँ"]},
{"paper":"GS Paper-I","subject":"History & Culture","topics":["भारत का इतिहास","भारतीय राष्ट्रीय आंदोलन","कला एवं संस्कृति से जुड़े प्रमुख आयाम"]},
{"paper":"GS Paper-I","subject":"Geography","topics":["भारत एवं विश्व का भौतिक भूगोल","भारत एवं विश्व का सामाजिक भूगोल","भारत एवं विश्व का आर्थिक भूगोल"]},
{"paper":"GS Paper-I","subject":"Polity & Governance","topics":["भारतीय संविधान","राजनीतिक व्यवस्था","पंचायती राज","लोक नीति","अधिकार संबंधी मुद्दे","शासन व्यवस्था"]},
{"paper":"GS Paper-I","subject":"Economy & Social Development","topics":["सतत विकास","गरीबी","समावेशन","जनसांख्यिकी","सामाजिक क्षेत्र की पहल","भारतीय अर्थव्यवस्था के मूल मुद्दे"]},
{"paper":"GS Paper-I","subject":"Environment","topics":["पर्यावरणीय पारिस्थितिकी","जैव विविधता","जलवायु परिवर्तन","सामान्य पर्यावरणीय मुद्दे"]},
{"paper":"GS Paper-I","subject":"General Science","topics":["सामान्य विज्ञान","विज्ञान एवं प्रौद्योगिकी के दैनिक जीवन से जुड़े अनुप्रयोग"]},
{"paper":"GS Paper-II (CSAT)","subject":"Comprehension","topics":["Reading Comprehension","Interpersonal and communication skills"]},
{"paper":"GS Paper-II (CSAT)","subject":"Reasoning","topics":["Logical reasoning","Analytical ability","Decision making","Problem solving","General mental ability"]},
{"paper":"GS Paper-II (CSAT)","subject":"Numeracy & Data","topics":["Basic numeracy (Class X level)","Data interpretation (Class X level)"]}]
MAINS=[
{"paper":"Paper-A Indian Language","subject":"Qualifying Indian Language","qualifying":True,"topics":["गद्यांश की समझ","संक्षिप्त लेखन","शब्द प्रयोग और शब्दावली","लघु निबंध","अंग्रेजी से भारतीय भाषा तथा भारतीय भाषा से अंग्रेजी अनुवाद"]},
{"paper":"Paper-B English","subject":"Qualifying English","qualifying":True,"topics":["Comprehension of given passages","Precis Writing","Usage and Vocabulary","Short Essays"]},
{"paper":"Essay","subject":"Essay","topics":["विभिन्न विषयों पर सुव्यवस्थित निबंध लेखन","विषय पर केंद्रित तर्क","स्पष्ट एवं सटीक अभिव्यक्ति"]},
{"paper":"GS-I","subject":"Indian Heritage & Culture","topics":["भारतीय कला रूप","साहित्य","वास्तुकला: प्राचीन से आधुनिक"]},
{"paper":"GS-I","subject":"Modern Indian History","topics":["18वीं सदी के मध्य से आधुनिक भारत","महत्वपूर्ण घटनाएँ, व्यक्तित्व और मुद्दे","स्वतंत्रता संग्राम के चरण एवं योगदान","स्वतंत्रता के बाद एकीकरण और पुनर्गठन"]},
{"paper":"GS-I","subject":"World History","topics":["औद्योगिक क्रांति","विश्व युद्ध","राष्ट्रीय सीमाओं का पुनर्निर्धारण","उपनिवेशवाद और उपनिवेश मुक्ति","राजनीतिक दर्शन और समाज पर प्रभाव"]},
{"paper":"GS-I","subject":"Indian Society","topics":["भारतीय समाज की प्रमुख विशेषताएँ","भारत की विविधता","महिलाएँ और महिला संगठन","जनसंख्या एवं संबंधित मुद्दे","गरीबी और विकास","शहरीकरण","वैश्वीकरण का भारतीय समाज पर प्रभाव","सामाजिक सशक्तिकरण","साम्प्रदायिकता","क्षेत्रवाद","धर्मनिरपेक्षता"]},
{"paper":"GS-I","subject":"Geography","topics":["विश्व का भौतिक भूगोल","प्राकृतिक संसाधनों का वितरण","उद्योगों के स्थान निर्धारण के कारक","भूकंप, सुनामी, ज्वालामुखी, चक्रवात जैसी भू-भौतिक घटनाएँ","भौगोलिक विशेषताओं एवं वनस्पति-जीव में परिवर्तन"]},
{"paper":"GS-II","subject":"Constitution & Polity","topics":["संविधान: विकास, विशेषताएँ, संशोधन और मूल संरचना","संघ एवं राज्यों के कार्य और उत्तरदायित्व","संघवाद और स्थानीय निकाय","शक्तियों का पृथक्करण","तुलनात्मक संवैधानिक योजनाएँ","संसद और राज्य विधानमंडल","कार्यपालिका और न्यायपालिका","दबाव समूह एवं औपचारिक-अनौपचारिक संघ","Representation of the People Act के प्रमुख प्रावधान","संवैधानिक पद एवं निकाय","वैधानिक, नियामक एवं अर्ध-न्यायिक निकाय"]},
{"paper":"GS-II","subject":"Governance & Social Justice","topics":["सरकारी नीतियाँ और क्रियान्वयन","विकास प्रक्रिया और विकास उद्योग","NGO, SHG एवं अन्य हितधारक","कल्याणकारी योजनाएँ और कमजोर वर्ग","स्वास्थ्य, शिक्षा और मानव संसाधन","गरीबी और भूख","शासन, पारदर्शिता और जवाबदेही","ई-गवर्नेंस","नागरिक चार्टर","लोक सेवाओं की भूमिका"]},
{"paper":"GS-II","subject":"International Relations","topics":["भारत और पड़ोसी","द्विपक्षीय, क्षेत्रीय एवं वैश्विक समूह","विकसित और विकासशील देशों की नीतियों का भारत पर प्रभाव","भारतीय प्रवासी","अंतरराष्ट्रीय संस्थाएँ, एजेंसियाँ एवं मंच"]},
{"paper":"GS-III","subject":"Economy","topics":["भारतीय अर्थव्यवस्था, योजना और संसाधन","वृद्धि, विकास और रोजगार","समावेशी विकास","सरकारी बजट","कृषि उपज, भंडारण, परिवहन और विपणन","ई-टेक्नोलॉजी और किसान","प्रत्यक्ष एवं अप्रत्यक्ष कृषि सहायता","PDS, बफर स्टॉक और खाद्य सुरक्षा","पशुपालन अर्थशास्त्र","खाद्य प्रसंस्करण","भूमि सुधार","उदारीकरण और औद्योगिक नीति","अवसंरचना","निवेश मॉडल"]},
{"paper":"GS-III","subject":"Science & Technology","topics":["विज्ञान एवं प्रौद्योगिकी के विकास और अनुप्रयोग","भारतीय उपलब्धियाँ","IT, Space, Computers, Robotics, Nano-tech, Bio-tech","बौद्धिक संपदा अधिकार"]},
{"paper":"GS-III","subject":"Environment & Disaster Management","topics":["संरक्षण","पर्यावरण प्रदूषण और क्षरण","पर्यावरण प्रभाव आकलन","आपदा और आपदा प्रबंधन"]},
{"paper":"GS-III","subject":"Internal Security","topics":["विकास और उग्रवाद का संबंध","बाह्य एवं गैर-राज्य कारक","संचार नेटवर्क से आंतरिक सुरक्षा चुनौतियाँ","मीडिया/सोशल मीडिया और सुरक्षा","साइबर सुरक्षा","मनी लॉन्ड्रिंग","सीमा क्षेत्रों की सुरक्षा","संगठित अपराध और आतंकवाद","सुरक्षा बल एवं एजेंसियाँ"]},
{"paper":"GS-IV","subject":"Ethics, Integrity & Aptitude","topics":["नैतिकता और मानवीय अंतःक्रिया","मानवीय मूल्य","दृष्टिकोण","सिविल सेवा के लिए योग्यता और मूलभूत मूल्य","भावनात्मक बुद्धिमत्ता","नैतिक चिंतक और दार्शनिक","लोक प्रशासन में नैतिकता","शासन में शुचिता","सूचना साझा करना और पारदर्शिता","RTI","आचार संहिता और नैतिक संहिता","नागरिक चार्टर","कार्य संस्कृति और सेवा वितरण","लोक निधि का उपयोग","भ्रष्टाचार की चुनौतियाँ","Case Studies"]}]
OPTIONAL_SUBJECTS=list(ALL_OPTIONALS)
def _decorate(rows):return [{**r,'source_url':OFFICIAL_NOTIFICATION_SOURCE,'verified_navigation':bool(r.get('topics'))} for r in rows]
def topic_names(section):
    out=[]
    for item in section.get('topics') or []:
        if isinstance(item,str):out.append(item)
        elif isinstance(item,dict) and (item.get('topic') or item.get('title')):out.append(item.get('topic') or item.get('title'))
    return out
def topic_is_loaded(exam,paper,subject,topic,subtopic=None):
    for section in syllabus_for(exam):
        if section.get('paper')!=paper or section.get('subject')!=subject:continue
        for item in section.get('topics') or []:
            if isinstance(item,str) and item==topic:return subtopic in (None,'')
            if isinstance(item,dict) and (item.get('topic') or item.get('title'))==topic:
                return subtopic in (None,'') or subtopic in (item.get('subtopics') or [])
    return False
def optional_catalog():return [{'subject':s,'source_url':OFFICIAL_NOTIFICATION_SOURCE,'papers':[{'paper':'Paper-I','topics':[]},{'paper':'Paper-II','topics':[]}],'detailed_topics_loaded':False,'verified_complete':False} for s in OPTIONAL_SUBJECTS]
def syllabus_for(exam):
    key=(exam or '').lower()
    if key=='prelims':return _decorate(PRELIMS)
    if key=='mains':return _decorate(MAINS)
    if key=='optional':return optional_catalog()
    return {'prelims':_decorate(PRELIMS),'mains':_decorate(MAINS),'optional':optional_catalog()}