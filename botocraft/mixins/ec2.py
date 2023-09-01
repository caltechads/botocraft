

class SecurityGroupMixin:

    def save(self, **kwargs):
        """
        Save the model.
        """
        if not self.pk:
            obj = self.objects.create(self, **kwargs)
            self.objects.authorize_ingress(obj.pk, self.IpPermissions, **kwargs)
        else:
            old_obj = self.objects.get(pk=self.pk)
            if self.IpPermissions != old_obj.IpPermissions:
                if old_obj.IpPermissions:
                    self.objects.revoke_ingress(self.pk, old_obj.IpPermissions, **kwargs)
                if self.IpPermissions:
                    self.objects.authorize_ingress(self.pk, self.IpPermissions, **kwargs)
