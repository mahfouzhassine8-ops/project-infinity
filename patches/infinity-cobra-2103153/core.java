// COBRA-APPEND
  /** Pure, host-tested rules shared by the live guide and all video surfaces. */
  private static final class CobraCore {
    interface Sink {
      void channel(String id, String name) throws Exception;
      void programme(Programme p) throws Exception;
    }
    static final class Programme {
      String id = "", title = "", description = "";
      long start, stop;
    }
    static String clean(String value) {
      return value == null ? "" : value.replace("\uFEFF", "").trim();
    }
    static String alias(String value) {
      return clean(value).replaceAll("\\s+", " ").toLowerCase(Locale.ROOT);
    }
    static long time(String value) {
      String v = clean(value);
      java.util.regex.Matcher m = Pattern.compile(
          "^(\\d{4}(?:\\d{2}){0,5})(?:\\s*(Z|[+-]\\d{2}:?\\d{2}))?$").matcher(v);
      if (!m.matches()) return 0;
      String date = m.group(1), zone = m.group(2);
      String pattern;
      switch (date.length()) {
        case 4: pattern = "yyyy"; break;
        case 6: pattern = "yyyyMM"; break;
        case 8: pattern = "yyyyMMdd"; break;
        case 10: pattern = "yyyyMMddHH"; break;
        case 12: pattern = "yyyyMMddHHmm"; break;
        case 14: pattern = "yyyyMMddHHmmss"; break;
        default: return 0;
      }
      SimpleDateFormat f = new SimpleDateFormat(pattern + " Z", Locale.US);
      f.setLenient(false);
      f.setTimeZone(TimeZone.getTimeZone("UTC"));
      if (zone == null || "Z".equals(zone)) zone = "+0000";
      zone = zone.replace(":", "");
      String input = date + " " + zone;
      java.text.ParsePosition pos = new java.text.ParsePosition(0);
      Date result = f.parse(input, pos);
      return result != null && pos.getIndex() == input.length() ? result.getTime() : 0;
    }
    static boolean current(long start, long stop, long now) {
      return start > 0 && start <= now && stop > now;
    }
    static int[] retained(List<String> oldIds, List<String> nextIds) {
      if (nextIds.size() > 4 || new HashSet<>(nextIds).size() != nextIds.size())
        throw new IllegalArgumentException("Multi-View requires unique channels, maximum four");
      int[] positions = new int[nextIds.size()];
      for (int i = 0; i < positions.length; i++) positions[i] = oldIds.indexOf(nextIds.get(i));
      return positions;
    }
    static float[] scales(int vw, int vh, int sw, int sh, float pixels,
                          int rotation, int mode, float customX, float customY) {
      if (vw <= 0 || vh <= 0 || sw <= 0 || sh <= 0) return new float[]{1f, 1f};
      float aspect = sw * (pixels > 0 ? pixels : 1f) / sh;
      if (rotation == 90 || rotation == 270) aspect = 1f / aspect;
      if (mode == 2) aspect = 16f / 9f;
      if (mode == 3) aspect = 4f / 3f;
      float w = Math.min(vw, vh * aspect), h = w / aspect;
      if (mode == 1) { w = Math.max(vw, vh * aspect); h = w / aspect; }
      float x = 1f, y = 1f;
      if (mode == 4) x = 1.10f;
      else if (mode == 5) x = 1.25f;
      else if (mode == 6) x = 1.40f;
      else if (mode == 7) { x = 1.24f; y = .84f; }
      else if (mode == 8) x = y = 1.25f;
      else if (mode == 9) x = y = 1.50f;
      else if (mode == 10) x = y = 2f;
      else if (mode == 11) {
        x = Math.max(.55f, Math.min(1.8f, customX));
        y = Math.max(.55f, Math.min(1.8f, customY));
      }
      return new float[]{w / vw * x, h / vh * y};
    }
    static void parse(InputStream stream, Sink sink) throws Exception {
      javax.xml.parsers.SAXParserFactory f = javax.xml.parsers.SAXParserFactory.newInstance();
      f.setNamespaceAware(false);
      f.setValidating(false);
      try { f.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true); } catch (Exception ignored) {}
      org.xml.sax.XMLReader reader = f.newSAXParser().getXMLReader();
      for (String feature : new String[]{
          "http://xml.org/sax/features/external-general-entities",
          "http://xml.org/sax/features/external-parameter-entities",
          "http://apache.org/xml/features/nonvalidating/load-external-dtd"}) {
        try { reader.setFeature(feature, false); } catch (org.xml.sax.SAXException ignored) {}
      }
      reader.setEntityResolver((publicId, systemId) ->
          new org.xml.sax.InputSource(new java.io.StringReader("")));
      reader.setContentHandler(new org.xml.sax.helpers.DefaultHandler() {
        Programme programme;
        String channelId = "", capture = "";
        final StringBuilder text = new StringBuilder();
        boolean root = false;
        int rows = 0; long expandedCharacters = 0;
        @Override public void startElement(String uri, String local, String name,
            org.xml.sax.Attributes attrs) throws org.xml.sax.SAXException {
          if (!root) {
            if (!"tv".equals(name)) throw new org.xml.sax.SAXException("Not XMLTV");
            root = true;
          }
          if ("programme".equals(name)) {
            if (++rows > 1500000) throw new org.xml.sax.SAXException("Guide safety limit");
            programme = new Programme();
            programme.id = clean(attrs.getValue("channel"));
            programme.start = time(attrs.getValue("start"));
            programme.stop = time(attrs.getValue("stop"));
          } else if ("channel".equals(name)) channelId = clean(attrs.getValue("id"));
          else if (programme != null && ("title".equals(name) || "desc".equals(name))) {
            capture = name; text.setLength(0);
          } else if (!channelId.isEmpty() && "display-name".equals(name)) {
            capture = name; text.setLength(0);
          }
        }
        @Override public void characters(char[] value, int start, int length) throws org.xml.sax.SAXException {
          expandedCharacters += length; if(expandedCharacters > 256L*1024L*1024L) throw new org.xml.sax.SAXException("Expanded guide safety limit");
          int max = "desc".equals(capture) ? 1024 : 256;
          if (!capture.isEmpty() && text.length() < max)
            text.append(value, start, Math.min(length, max - text.length()));
        }
        @Override public void endElement(String uri, String local, String name)
            throws org.xml.sax.SAXException {
          try {
            if (name.equals(capture)) {
              String value = clean(text.toString());
              if (programme != null && "title".equals(name) && programme.title.isEmpty())
                programme.title = value;
              else if (programme != null && "desc".equals(name) && programme.description.isEmpty())
                programme.description = value;
              else if ("display-name".equals(name)) sink.channel(channelId, value);
              capture = "";
            }
            if ("channel".equals(name)) { sink.channel(channelId, ""); channelId = ""; }
            if ("programme".equals(name) && programme != null) {
              if (!programme.id.isEmpty() && programme.start > 0) sink.programme(programme);
              programme = null; capture = "";
            }
          } catch (Exception error) { throw new org.xml.sax.SAXException(error); }
        }
        @Override public void endDocument() throws org.xml.sax.SAXException {
          if (!root) throw new org.xml.sax.SAXException("Empty guide");
        }
      });
      reader.parse(new org.xml.sax.InputSource(stream));
    }
  }
