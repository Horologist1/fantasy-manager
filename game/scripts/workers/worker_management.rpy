# worker_management.rpy
init python:

    def find_worker_by_name(name):
            """
            Search for a worker in the store.workers list by their name.
            Returns the worker dictionary if found, or None if not.
            """
            for worker in store.workers:
                if worker.get("name") == name:
                    return worker
            # Optionally, search in available_workers if needed:
            for worker in store.available_workers:
                if worker.get("name") == name:
                    return worker
            return None

    def navigate_worker(direction):
        # Check if the workers list is empty.
        if len(store.workers) == 0:
            renpy.notify("No workers available.")
            return
        # Update the global current_worker_index based on the button pressed.
        if direction == "prev":
            store.current_worker_index = (store.current_worker_index - 1) % len(store.workers)
        elif direction == "next":
            store.current_worker_index = (store.current_worker_index + 1) % len(store.workers)
        else:
            return
        # Get the worker at the new index.
        new_worker = store.workers[store.current_worker_index]
        # Update the screen variable for the worker image.
        store.current_image = get_worker_image(new_worker)
        # Show the worker_details screen, passing the new worker.
        renpy.call_in_new_context("worker_details", worker=new_worker)

    def get_sell_info(worker):
        if worker.get("is_servant", False):
            return ("Sell", [Function(unassign_worker, worker), Function(workers.remove, worker), SetVariable("money", money + (worker.get("level", 1) * 500))])
        else:
            return ("Fire", [Function(unassign_worker, worker), Function(workers.remove, worker)])

    def sell_worker(worker):
        """
        Sells (or fires) a worker.
        If worker["is_servant"] is True, the worker is sold (refunded);
        otherwise, the worker is simply fired.
        """
        if worker.get("is_servant", False):
            unassign_worker(worker)
            if worker in workers:
                workers.remove(worker)
            store.money += worker.get("level", 1) * 500
        else:
            unassign_worker(worker)
            if worker in workers:
                    workers.remove(worker)


    def get_sell_text(worker):
        """
        Returns "Sell" if worker["is_servant"] is True; otherwise, "Fire".
        """
        return "Sell" if worker.get("is_servant", False) else "Fire"

    def add_to_dead_workers(worker_name):
        """
        Add a worker's name to the dead_worker_names list if not already present.
        """
        if worker_name not in store.dead_worker_names:
            store.dead_worker_names.append(worker_name)
            renpy.log(f"Added {worker_name} to dead worker list")

    def is_worker_dead(worker_name):
        """
        Check if a worker's name is in the dead_worker_names list.
        """
        return worker_name in store.dead_worker_names

# Initialize dead_worker_names list
default dead_worker_names = []
