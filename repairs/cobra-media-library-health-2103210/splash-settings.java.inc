  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra = "live".equals(experience);
    final String title = cobra ? "Cobra options" : "Infinity options";
    final String label = cobra ? "Cobra" : "Infinity";
    final String[] options = cobra ? new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Kodi Health Center",
        "Cobra Recovery"
    } : new String[]{
        "Remember & launch " + label,
        "Launch " + label + " just this time",
        "Ask every time",
        "Kodi Health Center"
    };
    (cobra ? new android.app.AlertDialog.Builder(this,"light".equals(chooserAppearanceMode())?android.R.style.Theme_Material_Light_Dialog_Alert:android.R.style.Theme_Material_Dialog_Alert)
        : new CobraVisualRenderer.DialogBuilder(this,vtheme(),"chooser.settings"))
        .setTitle(title)
        .setItems(options, (dialog, which) -> {
          if (which == 0)
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .putString(INFINITY_EXPERIENCE_DEFAULT, experience).apply();
            launchInfinityExperience(experience);
          }
          else if (which == 1)
          {
            launchInfinityExperience(experience);
          }
          else if (which == 3)
          {
            launchKodiHealthCenter();
          }
          else if(which==4&&cobra)
          {
            showCobraRecovery();
          }
          else
          {
            getSharedPreferences(INFINITY_EXPERIENCE_PREFS, MODE_PRIVATE).edit()
                .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
            android.widget.Toast.makeText(this,
                "Infinity will ask which experience to open next time.",
                android.widget.Toast.LENGTH_SHORT).show();
          }
        })
        .setNegativeButton("Cancel", null)
        .show();
  }

  private void launchKodiHealthCenter()
  {
    Intent intent = new Intent(this, @APP_PACKAGE@.Main.class);
    intent.putExtra("infinity_launch_kodi_health_center", true);
    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
    startActivity(intent);
    finish();
  }

