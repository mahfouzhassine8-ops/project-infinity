package qa.external;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import java.io.File;
import java.io.FileNotFoundException;

/** Disposable real SAF provider, never included in the delivered APK. */
public final class ResumeDocuments extends DocumentsProvider {
    public boolean onCreate(){return true;}
    public Cursor queryRoots(String[] projection){return new MatrixCursor(new String[]{DocumentsContract.Root.COLUMN_ROOT_ID});}
    public Cursor queryDocument(String id,String[] projection)throws FileNotFoundException{
        File file=file(id);
        MatrixCursor cursor=new MatrixCursor(new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,
            DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_LAST_MODIFIED});
        cursor.addRow(new Object[]{id,id,"video/mp4",file.length(),file.lastModified()});return cursor;
    }
    public Cursor queryChildDocuments(String id,String[] projection,String sort){return new MatrixCursor(new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID});}
    public boolean isChildDocument(String parent,String child){return "root".equals(parent)&&"a.mp4".equals(child);}
    public ParcelFileDescriptor openDocument(String id,String mode,CancellationSignal signal)throws FileNotFoundException{
        return ParcelFileDescriptor.open(file(id),ParcelFileDescriptor.MODE_READ_ONLY);
    }
    private File file(String id)throws FileNotFoundException{
        if(!"a.mp4".equals(id))throw new FileNotFoundException();
        return new File(getContext().getFilesDir(),id);
    }
}
