package org.xmlpull.v1;
public interface XmlPullParser {
 int START_DOCUMENT=0,END_DOCUMENT=1,START_TAG=2,END_TAG=3,TEXT=4;
 void setFeature(String name,boolean value) throws XmlPullParserException;
 void setInput(java.io.InputStream stream,String encoding) throws XmlPullParserException;
 int getEventType() throws XmlPullParserException;
 int next() throws XmlPullParserException,java.io.IOException;
 String getName();String getText();String getAttributeValue(String namespace,String name);
}