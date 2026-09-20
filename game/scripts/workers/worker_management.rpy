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

    def get_worker_sell_refund(worker):
        """Single source for a servant's sale refund (shown in the confirm dialog, paid here)."""
        try:
            return max(1, int((worker or {}).get("level", 1) or 1)) * 500
        except (TypeError, ValueError):
            return 500

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
            store.money += get_worker_sell_refund(worker)
        else:
            unassign_worker(worker)
            if worker in workers:
                    workers.remove(worker)


    def get_sell_text(worker):
        """
        Returns "Sell" if worker["is_servant"] is True; otherwise, "Fire".
        """
        if not worker:
            return "Fire"
        return "Sell" if worker.get("is_servant", False) else "Fire"

    def add_to_dead_workers(worker_name):
        """
        Add a worker's name to the dead_worker_names list if not already present.
        """
        church_record_legacy_death_name(worker_name)

    def is_worker_dead(worker_name):
        """
        Check if a worker's name is in the dead_worker_names list.
        """
        return church_worker_is_dead(worker_name)

    def worker_can_reform(worker):
        """True if any of the worker's traits declares reform_on_death (e.g. the Slime race)."""
        if worker is None:
            return False
        for trait_name in (worker.get("traits") or []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if not trait_def:
                trait_def = get_trait_definition(trait_name)
            if trait_def and trait_def.get("reform_on_death"):
                return True
        return False

# Initialize dead_worker_names list
default dead_worker_names = []
