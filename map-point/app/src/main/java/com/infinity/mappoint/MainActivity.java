package com.infinity.mappoint;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final double DEST_LAT = 42.339788;
    private static final double DEST_LON = -83.287457;

    private static final String MAP_URL =
            "https://maps.apple.com/search?center=42.339788%2C-83.287457&span=0.016917%2C0.012153";

    private static final String GOOGLE_NAVIGATION_URI =
            "google.navigation:q=42.339788,-83.287457&mode=d";

    private static final String WEB_DIRECTIONS_URL =
            "https://www.google.com/maps/dir/?api=1&destination=42.339788,-83.287457&travelmode=driving";

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        FrameLayout root = new FrameLayout(this);

        webView = new WebView(this);
        root.addView(
                webView,
                new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT));

        Button directions = new Button(this);
        directions.setText("Directions");
        directions.setTextColor(Color.WHITE);
        directions.setTextSize(16f);
        directions.setAllCaps(false);
        directions.setPadding(dp(22), dp(12), dp(22), dp(12));

        GradientDrawable buttonBackground = new GradientDrawable();
        buttonBackground.setColor(0xE61C1C1E);
        buttonBackground.setCornerRadius(dp(24));
        directions.setBackground(buttonBackground);

        FrameLayout.LayoutParams buttonParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        buttonParams.bottomMargin = dp(22);
        root.addView(directions, buttonParams);

        directions.setOnClickListener(v -> launchDirections());

        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();

                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    return false;
                }

                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                }
                return true;
            }
        });

        if (savedInstanceState == null) {
            webView.loadUrl(MAP_URL);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    private void launchDirections() {
        Intent googleMaps = new Intent(Intent.ACTION_VIEW, Uri.parse(GOOGLE_NAVIGATION_URI));
        googleMaps.setPackage("com.google.android.apps.maps");

        if (googleMaps.resolveActivity(getPackageManager()) != null) {
            startActivity(googleMaps);
            return;
        }

        Intent browserDirections = new Intent(Intent.ACTION_VIEW, Uri.parse(WEB_DIRECTIONS_URL));
        if (browserDirections.resolveActivity(getPackageManager()) != null) {
            startActivity(browserDirections);
            return;
        }

        Toast.makeText(this, "No navigation app is available.", Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
