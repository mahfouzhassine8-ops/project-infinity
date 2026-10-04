package com.infinity.mappoint;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;
import org.osmdroid.config.Configuration;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.CopyrightOverlay;
import org.osmdroid.views.overlay.Marker;
import org.osmdroid.views.overlay.Polyline;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity implements LocationListener, TextToSpeech.OnInitListener {
    private static final int LOCATION_REQUEST = 42;

    // Fixed destination supplied by the user.
    private static final double DEST_LAT = 42.339788;
    private static final double DEST_LON = -83.287457;
    private static final String DEST_LABEL = "7932 N Gulley Rd";

    private static final long LOCATION_MIN_TIME_MS = 1000L;
    private static final float LOCATION_MIN_DISTANCE_M = 2f;
    private static final float REROUTE_DISTANCE_M = 90f;
    private static final long REROUTE_COOLDOWN_MS = 20000L;

    private MapView mapView;
    private Marker currentMarker;
    private Marker destinationMarker;
    private Polyline routeLine;

    private TextView maneuverText;
    private TextView maneuverDetail;
    private TextView routeSummary;
    private TextView destinationText;
    private Button goButton;
    private Button recenterButton;

    private LocationManager locationManager;
    private Location lastLocation;
    private RouteData routeData;

    private final ExecutorService networkExecutor = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private TextToSpeech tts;
    private boolean ttsReady = false;
    private boolean navigating = false;
    private int routeStepIndex = 0;
    private boolean announcedFar = false;
    private boolean announcedNear = false;
    private long lastRerouteAt = 0L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);

        Configuration.getInstance().setUserAgentValue(getPackageName());

        tts = new TextToSpeech(this, this);
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);

        buildUi();
        setupMap();

        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED) {
            startLocationUpdates();
        } else {
            requestPermissions(
                    new String[] {
                            Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION
                    },
                    LOCATION_REQUEST);
        }
    }

    private void buildUi() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(242, 242, 247));

        mapView = new MapView(this);
        root.addView(
                mapView,
                new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout topCard = new LinearLayout(this);
        topCard.setOrientation(LinearLayout.VERTICAL);
        topCard.setPadding(dp(18), dp(14), dp(18), dp(14));
        topCard.setBackground(roundRect(Color.WHITE, 24));
        topCard.setElevation(dp(8));

        maneuverText = new TextView(this);
        maneuverText.setText("Getting your route…");
        maneuverText.setTextColor(Color.BLACK);
        maneuverText.setTextSize(24f);
        maneuverText.setTypeface(null, android.graphics.Typeface.BOLD);

        maneuverDetail = new TextView(this);
        maneuverDetail.setText("Waiting for live GPS");
        maneuverDetail.setTextColor(Color.rgb(90, 90, 95));
        maneuverDetail.setTextSize(15f);
        maneuverDetail.setPadding(0, dp(4), 0, 0);

        topCard.addView(maneuverText);
        topCard.addView(maneuverDetail);

        FrameLayout.LayoutParams topParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.TOP);
        topParams.setMargins(dp(14), dp(14), dp(14), 0);
        root.addView(topCard, topParams);

        LinearLayout bottomCard = new LinearLayout(this);
        bottomCard.setOrientation(LinearLayout.VERTICAL);
        bottomCard.setPadding(dp(18), dp(14), dp(18), dp(16));
        bottomCard.setBackground(roundRect(Color.WHITE, 28));
        bottomCard.setElevation(dp(10));

        destinationText = new TextView(this);
        destinationText.setText(DEST_LABEL);
        destinationText.setTextColor(Color.BLACK);
        destinationText.setTextSize(18f);
        destinationText.setTypeface(null, android.graphics.Typeface.BOLD);

        routeSummary = new TextView(this);
        routeSummary.setText("Locating you…");
        routeSummary.setTextColor(Color.rgb(90, 90, 95));
        routeSummary.setTextSize(15f);
        routeSummary.setPadding(0, dp(3), 0, dp(12));

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER_VERTICAL);

        recenterButton = new Button(this);
        recenterButton.setText("◎");
        recenterButton.setTextSize(24f);
        recenterButton.setAllCaps(false);
        recenterButton.setTextColor(Color.rgb(0, 122, 255));
        recenterButton.setBackground(roundRect(Color.rgb(237, 237, 242), 22));
        recenterButton.setOnClickListener(v -> recenter());

        goButton = new Button(this);
        goButton.setText("GO");
        goButton.setAllCaps(false);
        goButton.setTextSize(22f);
        goButton.setTypeface(null, android.graphics.Typeface.BOLD);
        goButton.setTextColor(Color.WHITE);
        goButton.setOnClickListener(v -> startNavigation());
        setGoEnabled(false);

        LinearLayout.LayoutParams recenterParams =
                new LinearLayout.LayoutParams(dp(58), dp(52));
        LinearLayout.LayoutParams goParams =
                new LinearLayout.LayoutParams(0, dp(56), 1f);
        goParams.leftMargin = dp(10);

        actions.addView(recenterButton, recenterParams);
        actions.addView(goButton, goParams);

        bottomCard.addView(destinationText);
        bottomCard.addView(routeSummary);
        bottomCard.addView(actions);

        FrameLayout.LayoutParams bottomParams = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM);
        bottomParams.setMargins(dp(14), 0, dp(14), dp(18));
        root.addView(bottomCard, bottomParams);

        setContentView(root);
    }

    private void setupMap() {
        mapView.setTileSource(TileSourceFactory.MAPNIK);
        mapView.setMultiTouchControls(true);
        mapView.setTilesScaledToDpi(true);
        mapView.getController().setZoom(14.5);
        mapView.getController().setCenter(new GeoPoint(DEST_LAT, DEST_LON));

        CopyrightOverlay copyright = new CopyrightOverlay(this);
        mapView.getOverlays().add(copyright);

        destinationMarker = new Marker(mapView);
        destinationMarker.setPosition(new GeoPoint(DEST_LAT, DEST_LON));
        destinationMarker.setTitle(DEST_LABEL);
        destinationMarker.setSubDescription("Destination");
        destinationMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM);
        mapView.getOverlays().add(destinationMarker);

        currentMarker = new Marker(mapView);
        currentMarker.setTitle("My Location");
        currentMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER);
    }

    private GradientDrawable roundRect(int color, int radiusDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radiusDp));
        return drawable;
    }

    private void setGoEnabled(boolean enabled) {
        goButton.setEnabled(enabled);
        goButton.setAlpha(enabled ? 1f : 0.55f);
        goButton.setBackground(roundRect(
                enabled ? Color.rgb(0, 122, 255) : Color.rgb(142, 142, 147),
                24));
    }

    private void startLocationUpdates() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            return;
        }

        boolean requested = false;

        if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
            locationManager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER,
                    LOCATION_MIN_TIME_MS,
                    LOCATION_MIN_DISTANCE_M,
                    this);
            requested = true;
        }

        if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
            locationManager.requestLocationUpdates(
                    LocationManager.NETWORK_PROVIDER,
                    2500L,
                    5f,
                    this);
            requested = true;
        }

        Location best = null;
        try {
            Location gps = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            Location network = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            if (gps != null && network != null) {
                best = gps.getTime() >= network.getTime() ? gps : network;
            } else {
                best = gps != null ? gps : network;
            }
        } catch (SecurityException ignored) {
        }

        if (best != null) {
            onLocationChanged(best);
        } else if (!requested) {
            maneuverText.setText("Turn on Location");
            maneuverDetail.setText("GPS or network location is required for navigation");
        }
    }

    @Override
    public void onLocationChanged(Location location) {
        lastLocation = location;
        updateCurrentMarker(location);

        if (routeData == null) {
            fetchRoute(location, false);
            return;
        }

        if (navigating) {
            updateNavigation(location);
        }
    }

    private void updateCurrentMarker(Location location) {
        GeoPoint point = new GeoPoint(location.getLatitude(), location.getLongitude());
        currentMarker.setPosition(point);

        if (!mapView.getOverlays().contains(currentMarker)) {
            mapView.getOverlays().add(currentMarker);
        }

        if (navigating) {
            mapView.getController().animateTo(point);
            mapView.getController().setZoom(17.5);
        }

        mapView.invalidate();
    }

    private void recenter() {
        if (lastLocation != null) {
            GeoPoint point = new GeoPoint(lastLocation.getLatitude(), lastLocation.getLongitude());
            mapView.getController().animateTo(point);
            mapView.getController().setZoom(navigating ? 17.5 : 15.5);
        } else {
            mapView.getController().animateTo(new GeoPoint(DEST_LAT, DEST_LON));
        }
    }

    private void fetchRoute(Location from, boolean isReroute) {
        final double fromLat = from.getLatitude();
        final double fromLon = from.getLongitude();

        mainHandler.post(() -> {
            maneuverText.setText(isReroute ? "Rerouting…" : "Finding fastest route…");
            maneuverDetail.setText("Using live traffic-free road routing");
            setGoEnabled(false);
        });

        networkExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                String url = String.format(
                        Locale.US,
                        "https://router.project-osrm.org/route/v1/driving/%.6f,%.6f;%.6f,%.6f"
                                + "?overview=full&geometries=geojson&steps=true&alternatives=true",
                        fromLon,
                        fromLat,
                        DEST_LON,
                        DEST_LAT);

                connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(15000);
                connection.setRequestProperty("User-Agent", getPackageName() + "/2.0");
                connection.setRequestProperty("Accept", "application/json");

                int code = connection.getResponseCode();
                if (code != HttpURLConnection.HTTP_OK) {
                    throw new IllegalStateException("Routing service returned HTTP " + code);
                }

                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(connection.getInputStream()));
                StringBuilder body = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    body.append(line);
                }
                reader.close();

                RouteData parsed = parseRoute(body.toString());
                mainHandler.post(() -> applyRoute(parsed, isReroute));
            } catch (Exception e) {
                String message = e.getMessage() == null ? "Unable to build route" : e.getMessage();
                mainHandler.post(() -> {
                    maneuverText.setText("Route unavailable");
                    maneuverDetail.setText(message);
                    routeSummary.setText("Check your internet connection and try again");
                    setGoEnabled(false);
                });
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        });
    }

    private RouteData parseRoute(String jsonText) throws Exception {
        JSONObject root = new JSONObject(jsonText);
        if (!"Ok".equalsIgnoreCase(root.optString("code"))) {
            throw new IllegalStateException("No drivable route found");
        }

        JSONArray routes = root.getJSONArray("routes");
        if (routes.length() == 0) {
            throw new IllegalStateException("No route returned");
        }

        JSONObject route = routes.getJSONObject(0);
        RouteData data = new RouteData();
        data.distanceMeters = route.getDouble("distance");
        data.durationSeconds = route.getDouble("duration");

        JSONArray coordinates = route
                .getJSONObject("geometry")
                .getJSONArray("coordinates");

        for (int i = 0; i < coordinates.length(); i++) {
            JSONArray pair = coordinates.getJSONArray(i);
            data.geometry.add(new GeoPoint(pair.getDouble(1), pair.getDouble(0)));
        }

        JSONArray legs = route.getJSONArray("legs");
        for (int legIndex = 0; legIndex < legs.length(); legIndex++) {
            JSONArray steps = legs.getJSONObject(legIndex).getJSONArray("steps");
            for (int i = 0; i < steps.length(); i++) {
                JSONObject stepJson = steps.getJSONObject(i);
                JSONObject maneuver = stepJson.getJSONObject("maneuver");
                JSONArray location = maneuver.getJSONArray("location");

                Step step = new Step();
                step.type = maneuver.optString("type", "continue");
                step.modifier = maneuver.optString("modifier", "");
                step.name = stepJson.optString("name", "");
                step.distanceMeters = stepJson.optDouble("distance", 0d);
                step.durationSeconds = stepJson.optDouble("duration", 0d);
                step.maneuverPoint = new GeoPoint(
                        location.getDouble(1),
                        location.getDouble(0));
                data.steps.add(step);
            }
        }

        if (data.geometry.isEmpty() || data.steps.isEmpty()) {
            throw new IllegalStateException("Incomplete route data");
        }

        return data;
    }

    private void applyRoute(RouteData data, boolean isReroute) {
        routeData = data;

        if (routeLine != null) {
            mapView.getOverlays().remove(routeLine);
        }

        routeLine = new Polyline();
        routeLine.setPoints(data.geometry);
        routeLine.setColor(Color.rgb(0, 122, 255));
        routeLine.setWidth(12f);
        mapView.getOverlays().add(1, routeLine);
        mapView.invalidate();

        routeSummary.setText(
                formatMinutes(data.durationSeconds)
                        + " • "
                        + formatDistance(data.distanceMeters));

        if (navigating || isReroute) {
            navigating = true;
            routeStepIndex = firstActionableStep(data.steps);
            announcedFar = false;
            announcedNear = false;
            maneuverText.setText("Route updated");
            maneuverDetail.setText(routeSummary.getText());
            speak("Route updated");
            if (lastLocation != null) {
                updateNavigation(lastLocation);
            }
        } else {
            maneuverText.setText("Fastest route ready");
            maneuverDetail.setText("Tap GO for turn-by-turn guidance");
            setGoEnabled(true);
            showRouteOverview();
        }
    }

    private void showRouteOverview() {
        if (routeData == null || routeData.geometry.isEmpty()) {
            return;
        }

        double minLat = Double.MAX_VALUE;
        double maxLat = -Double.MAX_VALUE;
        double minLon = Double.MAX_VALUE;
        double maxLon = -Double.MAX_VALUE;

        for (GeoPoint p : routeData.geometry) {
            minLat = Math.min(minLat, p.getLatitude());
            maxLat = Math.max(maxLat, p.getLatitude());
            minLon = Math.min(minLon, p.getLongitude());
            maxLon = Math.max(maxLon, p.getLongitude());
        }

        org.osmdroid.util.BoundingBox box = new org.osmdroid.util.BoundingBox(
                maxLat, maxLon, minLat, minLon);

        mapView.zoomToBoundingBox(box, true, dp(70));
    }

    private void startNavigation() {
        if (routeData == null || lastLocation == null) {
            Toast.makeText(this, "Waiting for a GPS route.", Toast.LENGTH_SHORT).show();
            return;
        }

        navigating = true;
        routeStepIndex = firstActionableStep(routeData.steps);
        announcedFar = false;
        announcedNear = false;
        setGoEnabled(false);
        goButton.setText("Navigating");

        speak("Starting navigation");
        updateNavigation(lastLocation);
    }

    private int firstActionableStep(List<Step> steps) {
        for (int i = 0; i < steps.size(); i++) {
            String type = steps.get(i).type;
            if (!"depart".equalsIgnoreCase(type)) {
                return i;
            }
        }
        return 0;
    }

    private void updateNavigation(Location location) {
        if (routeData == null || routeData.steps.isEmpty()) {
            return;
        }

        GeoPoint current = new GeoPoint(location.getLatitude(), location.getLongitude());
        mapView.getController().animateTo(current);
        mapView.getController().setZoom(17.5);

        float offRoute = distanceToRouteMeters(current, routeData.geometry);
        long now = System.currentTimeMillis();

        if (offRoute > REROUTE_DISTANCE_M
                && now - lastRerouteAt > REROUTE_COOLDOWN_MS) {
            lastRerouteAt = now;
            fetchRoute(location, true);
            return;
        }

        if (routeStepIndex >= routeData.steps.size()) {
            arrive();
            return;
        }

        Step step = routeData.steps.get(routeStepIndex);
        float metersToManeuver = distanceMeters(current, step.maneuverPoint);
        String instruction = instructionFor(step);

        maneuverText.setText(instruction);
        maneuverDetail.setText(
                "In "
                        + formatDistance(metersToManeuver)
                        + " • "
                        + formatRemainingSummary(metersToManeuver));

        if (!announcedFar && metersToManeuver <= 500f && metersToManeuver > 160f) {
            speak("In " + formatDistanceSpoken(metersToManeuver) + ", " + instruction);
            announcedFar = true;
        }

        if (!announcedNear && metersToManeuver <= 160f && metersToManeuver > 35f) {
            speak("In " + formatDistanceSpoken(metersToManeuver) + ", " + instruction);
            announcedNear = true;
        }

        if (metersToManeuver <= 35f) {
            if ("arrive".equalsIgnoreCase(step.type)) {
                arrive();
                return;
            }

            speak(instruction);
            routeStepIndex++;
            announcedFar = false;
            announcedNear = false;

            if (routeStepIndex < routeData.steps.size()) {
                Step next = routeData.steps.get(routeStepIndex);
                maneuverText.setText(instructionFor(next));
            } else {
                arrive();
            }
        }

        routeSummary.setText(formatRemainingSummary(metersToManeuver));
    }

    private String formatRemainingSummary(float metersToManeuver) {
        if (routeData == null) {
            return "";
        }

        double remainingMeters = metersToManeuver;
        double remainingSeconds = 0d;

        for (int i = routeStepIndex; i < routeData.steps.size(); i++) {
            Step step = routeData.steps.get(i);
            remainingMeters += step.distanceMeters;
            remainingSeconds += step.durationSeconds;
        }

        return formatMinutes(remainingSeconds) + " • " + formatDistance(remainingMeters);
    }

    private void arrive() {
        navigating = false;
        maneuverText.setText("You’ve arrived");
        maneuverDetail.setText(DEST_LABEL);
        routeSummary.setText("Destination reached");
        goButton.setText("GO");
        setGoEnabled(false);
        speak("You have arrived at your destination");
        mapView.getController().animateTo(new GeoPoint(DEST_LAT, DEST_LON));
    }

    private String instructionFor(Step step) {
        String type = step.type == null ? "" : step.type.toLowerCase(Locale.US);
        String modifier = step.modifier == null ? "" : step.modifier.toLowerCase(Locale.US);
        String road = (step.name == null || step.name.trim().isEmpty())
                ? ""
                : " onto " + step.name.trim();

        if ("arrive".equals(type)) {
            return "Arrive at your destination";
        }

        if ("depart".equals(type)) {
            return modifier.isEmpty()
                    ? "Start route" + road
                    : "Head " + modifier + road;
        }

        if ("turn".equals(type) || "continue".equals(type) || "new name".equals(type)) {
            if (modifier.contains("uturn")) {
                return "Make a U-turn" + road;
            }
            if (modifier.contains("left")) {
                return "Turn " + modifier + road;
            }
            if (modifier.contains("right")) {
                return "Turn " + modifier + road;
            }
            if ("straight".equals(modifier)) {
                return "Continue straight" + road;
            }
            return "Continue" + road;
        }

        if ("merge".equals(type)) {
            return "Merge " + (modifier.isEmpty() ? "" : modifier + " ") + road.trim();
        }

        if ("on ramp".equals(type)) {
            return "Take the ramp" + road;
        }

        if ("off ramp".equals(type)) {
            return "Take the exit" + road;
        }

        if ("fork".equals(type)) {
            return "Keep " + (modifier.isEmpty() ? "ahead" : modifier) + road;
        }

        if ("end of road".equals(type)) {
            return "At the end of the road, turn "
                    + (modifier.isEmpty() ? "ahead" : modifier)
                    + road;
        }

        if ("roundabout".equals(type) || "rotary".equals(type)) {
            return "Enter the roundabout" + road;
        }

        return "Continue" + road;
    }

    private float distanceToRouteMeters(GeoPoint current, List<GeoPoint> geometry) {
        float min = Float.MAX_VALUE;
        int stride = Math.max(1, geometry.size() / 400);

        for (int i = 0; i < geometry.size(); i += stride) {
            float d = distanceMeters(current, geometry.get(i));
            if (d < min) {
                min = d;
            }
        }

        GeoPoint last = geometry.get(geometry.size() - 1);
        min = Math.min(min, distanceMeters(current, last));
        return min;
    }

    private float distanceMeters(GeoPoint a, GeoPoint b) {
        float[] result = new float[1];
        Location.distanceBetween(
                a.getLatitude(),
                a.getLongitude(),
                b.getLatitude(),
                b.getLongitude(),
                result);
        return result[0];
    }

    private String formatMinutes(double seconds) {
        int minutes = Math.max(1, (int) Math.round(seconds / 60d));
        if (minutes < 60) {
            return minutes + " min";
        }
        int hours = minutes / 60;
        int remain = minutes % 60;
        return remain == 0 ? hours + " hr" : hours + " hr " + remain + " min";
    }

    private String formatDistance(double meters) {
        if (meters >= 1609.344) {
            return String.format(Locale.US, "%.1f mi", meters / 1609.344);
        }
        int feet = (int) Math.round(meters * 3.28084);
        return feet + " ft";
    }

    private String formatDistanceSpoken(double meters) {
        if (meters >= 402.336) {
            return String.format(Locale.US, "%.1f miles", meters / 1609.344);
        }
        int feet = (int) Math.round(meters * 3.28084 / 50d) * 50;
        return Math.max(50, feet) + " feet";
    }

    private void speak(String text) {
        if (ttsReady && text != null && !text.trim().isEmpty()) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "map-point-nav");
        }
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            ttsReady = true;
            tts.setLanguage(Locale.US);
        }
    }

    @Override
    public void onProviderEnabled(String provider) {
    }

    @Override
    public void onProviderDisabled(String provider) {
        if (LocationManager.GPS_PROVIDER.equals(provider) && navigating) {
            maneuverDetail.setText("GPS signal lost — waiting for location");
        }
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onStatusChanged(String provider, int status, Bundle extras) {
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == LOCATION_REQUEST) {
            boolean granted =
                    grantResults.length > 0
                            && grantResults[0] == PackageManager.PERMISSION_GRANTED;

            if (granted) {
                startLocationUpdates();
            } else {
                maneuverText.setText("Location permission required");
                maneuverDetail.setText("Allow location to calculate and follow a route");
                routeSummary.setText("Navigation unavailable without location");
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (mapView != null) {
            mapView.onResume();
        }
    }

    @Override
    protected void onPause() {
        if (mapView != null) {
            mapView.onPause();
        }
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        try {
            locationManager.removeUpdates(this);
        } catch (Exception ignored) {
        }

        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }

        networkExecutor.shutdownNow();
        super.onDestroy();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static final class RouteData {
        final List<GeoPoint> geometry = new ArrayList<>();
        final List<Step> steps = new ArrayList<>();
        double distanceMeters;
        double durationSeconds;
    }

    private static final class Step {
        GeoPoint maneuverPoint;
        String type;
        String modifier;
        String name;
        double distanceMeters;
        double durationSeconds;
    }
}
