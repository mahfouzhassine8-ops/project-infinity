package qa.external;
import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.*;
/** Real provider grant boundary, not a mocked ContentResolver. */
public final class SourceProvider extends ContentProvider {
    public boolean onCreate(){return true;}
    public String getType(Uri uri){return "video/mp4";}
    public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        String name=uri.getLastPathSegment();
        if(name==null||!name.matches("(a|b|c|end|bad|audio)\\.mp4"))throw new FileNotFoundException();
        return ParcelFileDescriptor.open(new File(getContext().getFilesDir(),name),ParcelFileDescriptor.MODE_READ_ONLY);
    }
    public Cursor query(Uri u,String[] p,String s,String[] a,String o){return null;}
    public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
    public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
    public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
}
