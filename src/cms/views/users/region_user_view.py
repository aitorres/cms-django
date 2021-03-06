from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...forms.users import RegionUserForm, RegionUserProfileForm
from ...models import Region, UserProfile


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class RegionUserView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.manage_region_users"
    raise_exception = True

    template_name = "users/region/user.html"
    base_context = {"current_menu_item": "region_users"}

    def get(self, request, *args, **kwargs):

        region = Region.get_current_region(request)

        # filter by region to make sure no users from other regions can be changed through this view
        user = (
            get_user_model()
            .objects.filter(
                id=kwargs.get("user_id"),
                profile__regions=region,
            )
            .first()
        )
        user_profile = UserProfile.objects.filter(user=user).first()

        region_user_form = RegionUserForm(instance=user)
        user_profile_form = RegionUserProfileForm(instance=user_profile)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": region_user_form,
                "user_profile_form": user_profile_form,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):

        region = Region.get_current_region(request)

        # filter by region to make sure no users from other regions can be changed through this view
        user_instance = (
            get_user_model()
            .objects.filter(
                id=kwargs.get("user_id"),
                profile__regions=region,
            )
            .first()
        )
        user_profile_instance = UserProfile.objects.filter(user=user_instance).first()

        region_user_form = RegionUserForm(request.POST, instance=user_instance)
        user_profile_form = RegionUserProfileForm(
            request.POST, instance=user_profile_instance
        )

        # TODO: error handling
        if region_user_form.is_valid() and user_profile_form.is_valid():

            user = region_user_form.save()
            user_profile_form.save(user=user, region=region)

            if region_user_form.has_changed() or user_profile_form.has_changed():
                if user_instance:
                    messages.success(request, _("User was successfully saved."))
                else:
                    messages.success(request, _("User was successfully created."))
                    return redirect(
                        "edit_region_user",
                        **{
                            "region_slug": region.slug,
                            "user_id": user.id,
                        }
                    )
            else:
                messages.info(request, _("No changes detected."))
        else:
            # TODO: improve messages for region users
            messages.error(request, _("Errors have occurred."))

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "user_form": region_user_form,
                "user_profile_form": user_profile_form,
            },
        )
