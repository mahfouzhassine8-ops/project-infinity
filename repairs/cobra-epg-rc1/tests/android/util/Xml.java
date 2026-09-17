package android.util;
import org.xmlpull.v1.*;import javax.xml.stream.*;
public final class Xml {
 public static XmlPullParser newPullParser(){return new Adapter();}
 static final class Adapter implements XmlPullParser {
  XMLStreamReader reader;int event=START_DOCUMENT;
  public void setFeature(String n,boolean v){}
  public void setInput(java.io.InputStream in,String encoding)throws XmlPullParserException{
   try{XMLInputFactory f=XMLInputFactory.newFactory();f.setProperty(XMLInputFactory.SUPPORT_DTD,false);f.setProperty("javax.xml.stream.isSupportingExternalEntities",false);reader=f.createXMLStreamReader(in);}
   catch(XMLStreamException e){throw new XmlPullParserException(e.toString());}
  }
  public int getEventType(){return event;}
  public int next()throws XmlPullParserException{
   try{while(reader.hasNext()){int e=reader.next();if(e==XMLStreamConstants.START_ELEMENT)return event=START_TAG;if(e==XMLStreamConstants.END_ELEMENT)return event=END_TAG;if(e==XMLStreamConstants.CHARACTERS||e==XMLStreamConstants.CDATA)return event=TEXT;}return event=END_DOCUMENT;}
   catch(XMLStreamException e){throw new XmlPullParserException(e.toString());}
  }
  public String getName(){return reader.getLocalName();}public String getText(){return reader.getText();}public String getAttributeValue(String ns,String name){return reader.getAttributeValue(ns,name);}
 }
}