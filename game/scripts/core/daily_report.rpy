#daily_report.rpy

init python:

    def generate_daily_report():
        """
        Generates the daily report structure.
        """
        return {
            "date": store.day,
            "events": [],
            "worker_summaries": [],
            "resources_gathered": {},
        }

    def add_event_to_report(report, event):
        report["events"].append(event)

    def add_worker_summary_to_report(report, summary):
        report["worker_summaries"].append(summary)

    def add_resource_to_report(report, resource_type, amount):
        if resource_type not in report["resources_gathered"]:
            report["resources_gathered"][resource_type] = 0
        report["resources_gathered"][resource_type] += amount

    def display_daily_report(report):
        """
        Simple textual report. You can improve this using Ren'Py screens.
        """
        renpy.say(None, f"Informe del día {report['date']}:")

        if report["events"]:
            renpy.say(None, "Eventos ocurridos:")
            for event in report["events"]:
                renpy.say(None, f"- {event.get('description', 'Evento sin descripción')}")

        if report["worker_summaries"]:
            renpy.say(None, "Resumen de trabajadores:")
            for summary in report["worker_summaries"]:
                renpy.say(None, f"- {summary}")

        if report["resources_gathered"]:
            renpy.say(None, "Recursos obtenidos:")
            for resource, amount in report["resources_gathered"].items():
                renpy.say(None, f"- {resource}: {amount}")
