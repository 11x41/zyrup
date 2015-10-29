from .base import Batch


class SimpleBatch(Batch):

    def create_or_update(self, f, z_objects_list):
        z_objects_list_count = len(z_objects_list)

    def delete(self, f, z_object_type, z_id_list):
        z_id_list_count = len(z_id_list)