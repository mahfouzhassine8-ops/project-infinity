package qa.external;

import android.app.UiAutomation;
import android.graphics.Rect;
import android.util.Base64;
import android.util.Xml;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.lang.reflect.Method;
import org.xmlpull.v1.XmlSerializer;

/** QA-only persistent OS observer. No idle wait, input injection or app callbacks. */
public final class ImmediateHierarchy {
    static int count;
    static String value(CharSequence s) { return s == null ? "" : s.toString(); }
    static void node(XmlSerializer xml, AccessibilityNodeInfo n, Rect window, int depth) throws Exception {
        if (++count > 2000 || depth > 100) throw new IllegalStateException("Bounded UI tree exceeded");
        Rect b = new Rect(); n.getBoundsInScreen(b);
        if (!n.isVisibleToUser() || !b.intersect(window)) return;
        xml.startTag(null,"node");
        xml.attribute(null,"text",value(n.getText()));
        xml.attribute(null,"content-desc",value(n.getContentDescription()));
        xml.attribute(null,"class",value(n.getClassName()));
        xml.attribute(null,"package",value(n.getPackageName()));
        xml.attribute(null,"resource-id",value(n.getViewIdResourceName()));
        xml.attribute(null,"enabled",Boolean.toString(n.isEnabled()));
        xml.attribute(null,"selected",Boolean.toString(n.isSelected()));
        xml.attribute(null,"bounds","["+b.left+","+b.top+"]["+b.right+","+b.bottom+"]");
        for (int i=0; i<n.getChildCount(); i++) {
            AccessibilityNodeInfo child=n.getChild(i);
            if (child!=null) try { node(xml,child,window,depth+1); } finally { child.recycle(); }
        }
        xml.endTag(null,"node");
    }
    public static void main(String[] args) throws Exception {
        String expected="/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:/data/local/tmp/InfinityExternalObserver.jar";
        if (!expected.equals(System.getProperty("java.class.path"))) throw new IllegalStateException("OS-only QA classpath required");
        Class<?> c=Class.forName("com.android.uiautomator.core.UiAutomationShellWrapper");
        Object wrapper=c.getConstructor().newInstance();
        c.getMethod("connect").invoke(wrapper);
        Method disconnect=c.getMethod("disconnect");
        try {
            c.getMethod("setCompressedLayoutHierarchy",boolean.class).invoke(wrapper,false);
            UiAutomation ui=(UiAutomation)c.getMethod("getUiAutomation").invoke(wrapper);
            android.accessibilityservice.AccessibilityServiceInfo info=ui.getServiceInfo();
            info.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
            ui.setServiceInfo(info);
            System.out.println("EXTERNAL_READY"); System.out.flush();
            BufferedReader input=new BufferedReader(new InputStreamReader(System.in));
            String command;
            while ((command=input.readLine())!=null && !command.equals("QUIT")) {
                if (!command.matches("SNAP [0-9]+")) throw new IllegalArgumentException("Snapshot only");
                AccessibilityNodeInfo root=ui.getRootInActiveWindow();
                StringWriter out=new StringWriter(); XmlSerializer xml=Xml.newSerializer(); xml.setOutput(out);
                xml.startTag(null,"hierarchy"); count=0;
                xml.attribute(null,"window-id",root==null ? "none" : Integer.toString(root.getWindowId()));
                if (root!=null) try {
                    root.refresh(); Rect window=new Rect(); root.getBoundsInScreen(window);
                    node(xml,root,window,0);
                } finally { root.recycle(); }
                xml.endTag(null,"hierarchy"); xml.flush();
                String encoded=Base64.encodeToString(out.toString().getBytes("UTF-8"),Base64.NO_WRAP);
                System.out.println("EXTERNAL_"+command.substring(5)+" "+encoded); System.out.flush();
            }
        } finally { disconnect.invoke(wrapper); }
    }
}
