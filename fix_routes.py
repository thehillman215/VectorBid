                    #!/usr/bin/env python3
                    """
                    Targeted fix for routes.py - Only updates the process_schedule function
                    to use PBS results instead of trip rankings
                    """

                    import re
                    import shutil
                    from pathlib import Path
                    from datetime import datetime

                    def backup_file(file_path):
                        """Create backup of a file."""
                        if file_path.exists():
                            backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}{file_path.suffix}')
                            shutil.copy2(file_path, backup_path)
                            print(f"✅ Backed up {file_path} to {backup_path}")
                            return backup_path
                        return None

                    def update_routes_file():
                        """Update the existing routes.py file with minimal PBS fixes."""

                        # Find the routes file
                        routes_path = Path("routes (3).py")
                        if not routes_path.exists():
                            routes_path = Path("src/api/routes.py")
                            if not routes_path.exists():
                                print("❌ Could not find routes.py file")
                                return False

                        print(f"🔧 Updating {routes_path}")

                        # Backup the original file
                        backup_path = backup_file(routes_path)

                        try:
                            # Read the current file
                            with open(routes_path, 'r') as f:
                                content = f.read()

                            # Find the specific return statement to replace
                            old_return = '''return render_template(
                            "results.html",
                            trips=top_trips,
                            preferences=preferences,
                            user=current_user if current_user.is_authenticated else None,
                        )'''

                            new_return = '''# Generate PBS filters from preferences
                        pbs_filters = natural_language_to_pbs_filters(preferences, trips)

                        # Store PBS analysis in session for download
                        session['last_analysis'] = {
                            'preferences': preferences,
                            'pbs_filters': pbs_filters,
                            'trips_analyzed': len(trips),
                            'month_tag': 'uploaded_file'
                        }

                        # Return PBS results instead of trip rankings
                        return render_template(
                            "pbs_results.html",
                            filters=pbs_filters,
                            preferences=preferences,
                            analysis={'trips_analyzed': len(trips)},
                            month_tag='uploaded_file'
                        )'''

                            # Replace the return statement
                            if old_return in content:
                                updated_content = content.replace(old_return, new_return)
                                print("✅ Found and updated the return statement")
                            else:
                                print("❌ Could not find exact return statement. Manual update needed.")
                                print("\nIn process_schedule function, replace:")
                                print('return render_template("results.html", trips=top_trips, preferences=preferences, user=current_user if current_user.is_authenticated else None)')
                                print("\nWith:")
                                print('pbs_filters = natural_language_to_pbs_filters(preferences, trips)')
                                print('session["last_analysis"] = {"preferences": preferences, "pbs_filters": pbs_filters}')
                                print('return render_template("pbs_results.html", filters=pbs_filters, preferences=preferences)')
                                return False

                            # Write the updated content
                            with open(routes_path, 'w') as f:
                                f.write(updated_content)

                            print("✅ Successfully updated routes.py")
                            return True

                        except Exception as e:
                            print(f"❌ Error: {e}")
                            if backup_path:
                                shutil.copy2(backup_path, routes_path)
                                print("Restored backup")
                            return False

                    if __name__ == "__main__":
                        print("🎯 VectorBid Routes.py Fix")
                        print("=" * 30)
                        update_routes_file()