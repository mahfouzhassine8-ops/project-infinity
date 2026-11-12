package com.projectinfinity.kodi;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

/** Bounded, sender-private adaptive manifest translation; never a generic proxy. */
final class InfinityCastAdaptive {
    enum Kind {MEDIA,HLS,DASH,KEY,TEXT}
    interface Links {
        String resource(URI uri,Kind kind) throws IOException;
        String template(URI base,String value,String id,String bandwidth) throws IOException;
    }
    static final int LIMIT=2*1024*1024;
    private static final Pattern ATTRIBUTE=Pattern.compile("(?:^|,)([A-Z0-9-]+)=(\"[^\"]*\"|[^,]*)");
    private static final Pattern URI_ATTRIBUTE=Pattern.compile("(?<=^|,)URI=\"([^\"]*)\"");
    static boolean adaptive(String mime) {return "application/vnd.apple.mpegurl".equals(mime) || "application/dash+xml".equals(mime);}
    static URI resolve(URI base,String value) throws IOException {
        if(value==null || value.isEmpty() || value.length()>65536 || value.contains("{$"))throw new IOException("unsupported_manifest_uri");
        try {
            URI uri=base.resolve(value);
            if(uri.getHost()==null || uri.getRawUserInfo()!=null || uri.getRawFragment()!=null ||
                !("http".equalsIgnoreCase(uri.getScheme()) || "https".equalsIgnoreCase(uri.getScheme())) ||
                ("https".equalsIgnoreCase(base.getScheme()) && !"https".equalsIgnoreCase(uri.getScheme())))throw new IOException("unsupported_manifest_uri");
            return uri;
        } catch(IllegalArgumentException invalid){throw new IOException("invalid_manifest_uri");}
    }
    static byte[] rewrite(byte[] input,String mime,URI base,Links links) throws IOException {
        if(input.length>LIMIT)throw new IOException("manifest_size_limit");
        return "application/dash+xml".equals(mime)?dash(input,base,links):hls(input,base,links);
    }
    private static String utf8(byte[] data) throws IOException {
        try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(data)).toString();}
        catch(Exception invalid){throw new IOException("manifest_encoding");}
    }
    private static String attribute(String line,String name) {
        int colon=line.indexOf(':');Matcher m=ATTRIBUTE.matcher(colon<0?"":line.substring(colon+1));
        while(m.find())if(name.equals(m.group(1))){String v=m.group(2);return v.startsWith("\"")?v.substring(1,v.length()-1):v;}
        return "";
    }
    private static byte[] hls(byte[] data,URI base,Links links) throws IOException {
        String input=utf8(data);if(input.startsWith("\ufeff"))input=input.substring(1);
        if(!input.startsWith("#EXTM3U"))throw new IOException("invalid_hls_manifest");
        String[] lines=input.split("\\r?\\n",-1);if(lines.length>30000)throw new IOException("manifest_entry_limit");
        StringBuilder out=new StringBuilder();boolean variant=false;
        for(String raw:lines) {
            String line=raw.trim();if(line.isEmpty())continue;
            if(!line.startsWith("#")) {
                out.append(links.resource(resolve(base,line),variant?Kind.HLS:Kind.MEDIA)).append('\n');variant=false;continue;
            }
            if(!line.startsWith("#EXT") && !line.equals("#EXTM3U"))continue;
            String tag=line.split(":",2)[0];
            if(tag.equals("#EXT-X-DEFINE") || tag.equals("#EXT-X-CONTENT-STEERING"))throw new IOException("unsupported_hls_extension");
            if(tag.equals("#EXT-X-SESSION-DATA"))continue;
            if(tag.equals("#EXT-X-KEY") || tag.equals("#EXT-X-SESSION-KEY")) {
                String method=attribute(line,"METHOD"),format=attribute(line,"KEYFORMAT");
                if(!(method.equals("NONE") || method.equals("AES-128")) || !(format.isEmpty() || format.equals("identity")))
                    throw new IOException("drm_or_unsupported_encryption");
            }
            if(line.contains("URI=")) {
                Kind kind=tag.equals("#EXT-X-KEY") || tag.equals("#EXT-X-SESSION-KEY")?Kind.KEY:
                    Arrays.asList("#EXT-X-MEDIA","#EXT-X-I-FRAME-STREAM-INF","#EXT-X-RENDITION-REPORT").contains(tag)?Kind.HLS:
                    Arrays.asList("#EXT-X-MAP","#EXT-X-PART","#EXT-X-PRELOAD-HINT").contains(tag)?Kind.MEDIA:null;
                if(kind==null)throw new IOException("unsupported_hls_uri_attribute");
                int colon=line.indexOf(':');String prefix=line.substring(0,colon+1),attrs=line.substring(colon+1);
                Matcher m=URI_ATTRIBUTE.matcher(attrs);StringBuffer next=new StringBuffer();int count=0;
                while(m.find()){count++;m.appendReplacement(next,Matcher.quoteReplacement("URI=\""+links.resource(resolve(base,m.group(1)),kind)+"\""));}
                m.appendTail(next);if(count!=1)throw new IOException("invalid_hls_uri_attribute");line=prefix+next;
            }
            if(tag.equals("#EXTINF")){int comma=line.indexOf(',');if(comma>=0)line=line.substring(0,comma+1);}
            // Do not pass unknown private endpoint attributes or comments through.
            String remaining=line.replaceAll("URI=\"http://[^\"]*\"", "URI=\"local\"");
            if(remaining.contains("://") || remaining.contains("{$"))throw new IOException("unsupported_private_manifest_field");
            out.append(line).append('\n');variant=tag.equals("#EXT-X-STREAM-INF");
        }
        byte[] result=out.toString().getBytes(StandardCharsets.UTF_8);if(result.length>LIMIT*2)throw new IOException("rewritten_manifest_size");return result;
    }
    private static List<Element> children(Element e,String name) {
        List<Element> out=new ArrayList<>();for(Node n=e.getFirstChild();n!=null;n=n.getNextSibling())
            if(n instanceof Element && (name==null || name.equals(n.getLocalName()) || name.equals(n.getNodeName())))out.add((Element)n);
        return out;
    }
    private static Element first(Element e,String name){List<Element> list=children(e,name);return list.isEmpty()?null:list.get(0);}
    private static void remove(Element e,String name){for(Element n:children(e,name))e.removeChild(n);}
    private static Element merge(Element previous,Element current) {
        if(current==null)return previous;
        Element copy=(Element)current.cloneNode(true);if(previous==null)return copy;
        for(int i=0;i<previous.getAttributes().getLength();i++){Node a=previous.getAttributes().item(i);if(!copy.hasAttribute(a.getNodeName()))copy.setAttribute(a.getNodeName(),a.getNodeValue());}
        for(String name:new String[]{"SegmentTimeline","Initialization","RepresentationIndex"})
            if(first(copy,name)==null && first(previous,name)!=null)copy.appendChild(previous.getOwnerDocument().importNode(first(previous,name),true));
        return copy;
    }
    private static void walk(Element node,URI inherited,Element inheritedTemplate,Element inheritedList,Element inheritedBase,Links links,int[] count) throws IOException {
        if(++count[0]>20000)throw new IOException("manifest_entry_limit");
        List<Element> bases=children(node,"BaseURL");URI base=bases.isEmpty()?inherited:resolve(inherited,bases.get(0).getTextContent().trim());
        Element template=merge(inheritedTemplate,first(node,"SegmentTemplate")),list=merge(inheritedList,first(node,"SegmentList")),segmentBase=merge(inheritedBase,first(node,"SegmentBase"));
        if(first(node,"SegmentTemplate")!=null){list=null;segmentBase=null;}
        if(first(node,"SegmentList")!=null){template=null;segmentBase=null;}
        if(first(node,"SegmentBase")!=null){template=null;list=null;}
        if("Representation".equals(node.getLocalName()) || "Representation".equals(node.getNodeName())) {
            String id=node.getAttribute("id"),bandwidth=node.getAttribute("bandwidth");
            remove(node,"BaseURL");remove(node,"SegmentTemplate");remove(node,"SegmentList");remove(node,"SegmentBase");
            if(template!=null) {
                for(String key:new String[]{"media","initialization","index"})if(template.hasAttribute(key))
                    template.setAttribute(key,links.template(base,template.getAttribute(key),id,bandwidth));
                node.appendChild(node.getOwnerDocument().importNode(template,true));
            } else {
                Element local=node.getOwnerDocument().createElementNS(node.getNamespaceURI(),"BaseURL");
                local.setTextContent(links.resource(base,Kind.MEDIA));node.insertBefore(local,node.getFirstChild());
                Element segments=list!=null?list:segmentBase;
                if(segments!=null) {
                    for(String child:new String[]{"Initialization","RepresentationIndex","SegmentURL"})for(Element e:children(segments,child))
                        for(String key:new String[]{"sourceURL","media","index"})if(e.hasAttribute(key))e.setAttribute(key,links.resource(resolve(base,e.getAttribute(key)),Kind.MEDIA));
                    node.appendChild(node.getOwnerDocument().importNode(segments,true));
                }
            }
            return;
        }
        for(Element child:children(node,null))if(Arrays.asList("Period","AdaptationSet","Representation").contains(child.getLocalName()))
            walk(child,base,template,list,segmentBase,links,count);
        remove(node,"BaseURL");remove(node,"SegmentTemplate");remove(node,"SegmentList");remove(node,"SegmentBase");
    }
    private static byte[] dash(byte[] input,URI base,Links links) throws IOException {
        try {
            // Reject DTDs before parsing, in addition to parser-level controls.
            String raw=utf8(input);if(raw.toUpperCase(Locale.ROOT).contains("<!DOCTYPE") || raw.toUpperCase(Locale.ROOT).contains("<!ENTITY"))throw new IOException("external_xml_refused");
            DocumentBuilderFactory factory=DocumentBuilderFactory.newInstance();factory.setNamespaceAware(true);
            factory.setExpandEntityReferences(false);factory.setXIncludeAware(false);
            Document document=factory.newDocumentBuilder().parse(new ByteArrayInputStream(input));Element root=document.getDocumentElement();
            if(!"MPD".equals(root.getLocalName()))throw new IOException("invalid_dash_manifest");
            NodeList all=root.getElementsByTagNameNS("*","*");if(all.getLength()>20000)throw new IOException("manifest_entry_limit");
            for(int i=0;i<all.getLength();i++) {
                Element e=(Element)all.item(i);if("ContentProtection".equals(e.getLocalName()))throw new IOException("drm_or_unsupported_encryption");
                for(int a=0;a<e.getAttributes().getLength();a++)if("http://www.w3.org/1999/xlink".equals(e.getAttributes().item(a).getNamespaceURI()))throw new IOException("external_xml_refused");
            }
            for(String name:new String[]{"Location","PatchLocation","ProgramInformation","ServiceDescription"})remove(root,name);
            for(Element utc:children(root,"UTCTiming")) {
                String scheme=utc.getAttribute("schemeIdUri");
                if(scheme.contains("http-xsdate") || scheme.contains("http-iso"))utc.setAttribute("value",links.resource(resolve(base,utc.getAttribute("value")),Kind.TEXT));
                else if(!scheme.contains("utc:direct:"))throw new IOException("unsupported_dash_clock");
            }
            walk(root,base,null,null,null,links,new int[]{0});
            TransformerFactory transformers=TransformerFactory.newInstance();
            transformers.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING,true);
            javax.xml.transform.Transformer transform=transformers.newTransformer();transform.setOutputProperty(OutputKeys.ENCODING,"UTF-8");
            ByteArrayOutputStream out=new ByteArrayOutputStream();transform.transform(new DOMSource(document),new StreamResult(out));
            if(out.size()>LIMIT*2)throw new IOException("rewritten_manifest_size");return out.toByteArray();
        } catch(IOException failure){throw failure;}catch(Exception invalid){throw new IOException("invalid_or_unsupported_dash_manifest");}
    }
}
