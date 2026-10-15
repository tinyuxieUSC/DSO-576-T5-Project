# 06 — App Setup, Default Settings, and Running Instructions

## Purpose

This part explains how to set up and run our Client Metadata Outreach Prioritizer dashboard. The goal is to make the app easy for the MetaBrainz project lead to use and easy for our team to maintain.

## 1. App Setup

Our project will use Python and Streamlit to build an interactive dashboard.

The app should have a simple setup process. It should load the configuration, connect to the prepared ListenBrainz data, and check that everything needed is available before showing the dashboard.

Only the data loading component should access the prepared data files. The setup component should not clean raw data or calculate MBID metrics.

## 2. Default Settings

I suggest keeping default settings in one configuration file so they are easy to update.

The settings should include:

- **Default page:** Client priority shortlist.
- **Date range:** A valid observation period agreed on by the team.
- **Bulk importers:** Excluded by default, subject to team agreement.
- **Minimum accounts:** A team-approved threshold.
- **Ranking weights:** Values agreed on with the ranking component.
- **Target MBID coverage:** A configurable percentage between 0% and 100%.

Users should be able to change these settings in the dashboard without editing the code.

## 3. Running Instructions

The final README should explain how to:

1. Install the required Python version and packages.
2. Obtain the prepared ListenBrainz data.
3. Set or change the default configuration.
4. Start the Streamlit dashboard.
5. Check that the app is running correctly.
6. Troubleshoot missing files or invalid settings.

The exact commands and file paths should match the final project structure agreed on by the team.

## 4. Input and Output

**Input:**

- Application configuration.
- Prepared data location from the data-loading component.
- Required dependencies and startup options.

**Output:**

- Validated application settings.
- A clear startup process.
- Helpful error messages when setup fails.

The setup component should provide configuration to the other pieces through clear interfaces. It should not directly change their internal data or calculation rules.

## 5. Error Handling

The application should check for common problems before running:

- Missing data or configuration files.
- Invalid date ranges.
- Negative minimum account counts.
- Ranking weights outside the agreed limits.
- Target MBID coverage outside 0%–100%.

If there is a problem, the app should display a clear message explaining what needs to be corrected.

## 6. Testing

We should test the setup with a small example dataset.

The tests should confirm that:

- The app starts with valid default settings.
- Missing files produce useful error messages.
- Invalid settings are rejected.
- Users can adjust settings without editing source code.
- A new team member can follow the README and start the app.

## 7. Design Decisions

I prefer keeping setup and configuration separate from data processing and visualization.

This follows the separation of concerns principle from Module 8. Each component should have one clear responsibility.

Keeping default settings in one place also makes future changes easier. If the team changes a default value, we should only need to update the configuration instead of several different files.

This design will make our dashboard easier to maintain, test, and run.