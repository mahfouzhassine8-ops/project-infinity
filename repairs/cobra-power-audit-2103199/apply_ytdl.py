"""Bound and close the inherited YTDL provider's HTTP work; native engine untouched."""
import hashlib

BASE_SOURCE_SHA256 = 'c4a41012de3af0e10678b864154d6f35126b91923391042fb9064534417ebbd6'

RESOLVER = '''  private static String getFinalURL(String url) throws IOException
  {
    URL current = new URL(url);
    for (int redirects = 0; redirects <= 20; redirects++)
    {
      if (!"http".equalsIgnoreCase(current.getProtocol())
          && !"https".equalsIgnoreCase(current.getProtocol()))
        throw new IOException("Unsupported media endpoint scheme");
      HttpURLConnection connection = null;
      try
      {
        connection = (HttpURLConnection) current.openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(15000);
        connection.setInstanceFollowRedirects(false);
        int status = connection.getResponseCode();
        if (status == HttpURLConnection.HTTP_MOVED_PERM || status == HttpURLConnection.HTTP_MOVED_TEMP)
        {
          String location = connection.getHeaderField("Location");
          if (location == null || location.trim().isEmpty() || redirects == 20)
            throw new IOException("Invalid or excessive media redirects");
          current = new URL(current, location);
          continue;
        }
        if (status >= 400 || status < 100)
          throw new IOException("Media endpoint returned an unsuccessful response");
        return current.toExternalForm();
      }
      finally
      {
        // The resolver only needs response headers. Disconnect the probe on
        // success, redirect and failure instead of leaking an unread stream.
        if (connection != null) connection.disconnect();
      }
    }
    throw new IOException("Excessive media redirects");
  }

'''

OPEN_FILE = '''  @Override
  public ParcelFileDescriptor openFile(Uri uri, String mode)
          throws FileNotFoundException
  {
    HttpURLConnection connection = null;
    InputStream input = null;
    ParcelFileDescriptor[] pipe = null;
    boolean handedOff = false;
    try
    {
      String decodedUrl = uri.getFragment();
      if (decodedUrl == null) throw new IOException("Missing media endpoint");
      URL url = new URL(getFinalURL(decodedUrl));
      connection = (HttpURLConnection) url.openConnection();
      connection.setConnectTimeout(15000);
      connection.setReadTimeout(15000);
      connection.setDoInput(true);
      input = connection.getInputStream();
      // Allocate descriptors only after connecting, then transfer ownership
      // atomically to the writer. Every earlier failure closes all resources.
      pipe = ParcelFileDescriptor.createPipe();
      new TransferThread(input,
              new ParcelFileDescriptor.AutoCloseOutputStream(pipe[1]), connection).start();
      handedOff = true;
      return pipe[0];
    }
    catch (IOException e)
    {
      Log.e(TAG, "XBMCYTDLContentProvider: media stream unavailable");
      throw new FileNotFoundException("Could not open media stream");
    }
    finally
    {
      if (!handedOff)
      {
        if (input != null) try { input.close(); } catch (IOException ignored) {}
        if (pipe != null) for (ParcelFileDescriptor descriptor : pipe)
          try { descriptor.close(); } catch (IOException ignored) {}
        if (connection != null) connection.disconnect();
      }
    }
  }

'''

TRANSFER = '''  static class TransferThread extends Thread
  {
    final InputStream in;
    final OutputStream out;
    final HttpURLConnection connection;

    TransferThread(InputStream in, OutputStream out, HttpURLConnection connection)
    {
      this.in = in;
      this.out = out;
      this.connection = connection;
    }

    @Override
    public void run()
    {
      byte[] buf = new byte[8192];
      try (InputStream source = in; OutputStream sink = out)
      {
        int len;
        while ((len = source.read(buf)) >= 0)
          sink.write(buf, 0, len);
        sink.flush();
      }
      catch (IOException ignored) {}
      finally
      {
        connection.disconnect();
      }
    }
  }

}
'''


def transform(text: str) -> str:
    if hashlib.sha256(text.encode()).hexdigest() != BASE_SOURCE_SHA256:
        raise RuntimeError('YTDL repair requires the exact inherited provider source')
    start = text.index('  private static String getFinalURL(')
    end = text.index('  @Override\n  public ParcelFileDescriptor openFile(', start)
    text = text[:start]+RESOLVER+text[end:]
    start = text.index('  @Override\n  public ParcelFileDescriptor openFile(')
    end = text.index('  @Override\n  public Cursor query(', start)
    text = text[:start]+OPEN_FILE+text[end:]
    start = text.index('  static class TransferThread extends Thread')
    text = text[:start]+TRANSFER
    return text.replace('import android.util.TimingLogger;\n', '', 1)
