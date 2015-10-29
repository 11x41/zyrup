from ..base import session_required


class Batch():

    _min_per_batch = _default_minimum_per_batch = 8
    _max_per_batch = _default_maximum_per_batch = 50

    def __init__(self):
        pass

    @session_required
    def create_or_update(self, f, z_objects_list):
        pass

    @session_required
    def delete(self, f, z_object_type, z_id_list):
        pass

    def set_batch_constraints(self, min_per_batch, max_per_batch):
        if min_per_batch in (None, 0):
            self._min_per_batch = self._default_batch_min
        if max_per_batch in (None, 0):
            self._max_per_batch = self._default_batch_max

        if min_per_batch > self._default_minimum_per_batch:
            raise ValueError("Min Batch Size must be set between 0 and %s, but recommended value is %s" %
                             (self._default_maximum_per_batch, self._default_minimum_per_batch))
        if max_per_batch > self._default_maximum_per_batch:
            raise ValueError("Max Batch Size must be set between 0 and %s" % self._default_maximum_per_batch)

        self._min_per_batch = int(min_per_batch)
        self._max_per_batch = int(max_per_batch)

    def get_batch_constraints(self):
        batch_min = self._default_minimum_per_batch
        batch_max = self._default_maximum_per_batch
        if self._min_per_batch:
            batch_min = self._min_per_batch
        if self._max_per_batch:
            batch_max = self._max_per_batch
        return batch_min, batch_max