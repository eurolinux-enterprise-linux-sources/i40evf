%define kmod_name		i40evf
%define kmod_driver_version	1.5.10_k
%define kmod_rpm_release	2
%define kmod_git_hash		40b15b9e0eb1b331906d70b561974ebbdf49730d
%define kmod_kernel_version	3.10.0-327.el7
%define kernel_version		3.10.0-327.el7
%define kmod_kbuild_dir		drivers/net/ethernet/intel/i40evf


%{!?dist: %define dist .el7}

Source0:	%{kmod_name}-%{kmod_driver_version}.tar.bz2
Source1:	%{kmod_name}.files
Source2:	depmodconf
Source3:	find-requires.ksyms
Source4:	find-provides.ksyms
Source5:	kmodtool
Source6:	i40evf.preamble
Source7:	symbols.greylist-x86_64
Source8:	symbols.greylist-ppc64
Source9:	symbols.greylist-ppc64le

Patch0:		i40evf.patch

%define __find_requires %_sourcedir/find-requires.ksyms
%define __find_provides %_sourcedir/find-provides.ksyms %{kmod_name} %{?epoch:%{epoch}:}%{version}-%{release}

Name:		%{kmod_name}
Version:	%{kmod_driver_version}
Release:	%{kmod_rpm_release}%{?dist}
Summary:	%{kmod_name} kernel module

Group:		System/Kernel
License:	GPLv2
URL:		http://www.kernel.org/
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:	kernel-devel = %kmod_kernel_version kmod
ExclusiveArch:  x86_64 ppc64 ppc64le


# Build only for standard kernel variant(s); for debug packages, append "debug"
# after "default" (separated by space)
%kernel_module_package -s %{SOURCE5} -f %{SOURCE1} -p %{SOURCE6} default

%description
%{kmod_name} - driver update

%prep
%setup
%patch0 -p1
set -- *
mkdir source
mv "$@" source/
cp %{SOURCE7} %{SOURCE8} %{SOURCE9} source/
mkdir obj

%build
for flavor in %flavors_to_build; do
	rm -rf obj/$flavor
	cp -r source obj/$flavor

	# update symvers file if existing
	symvers=source/Module.symvers-%{_target_cpu}
	if [ -e $symvers ]; then
		cp $symvers obj/$flavor/%{kmod_kbuild_dir}/Module.symvers
	fi

	make -C %{kernel_source $flavor} M=$PWD/obj/$flavor/%{kmod_kbuild_dir} \
		NOSTDINC_FLAGS="-I $PWD/obj/$flavor/include"

	# mark modules executable so that strip-to-file can strip them
	find obj/$flavor/%{kmod_kbuild_dir} -name "*.ko" -type f -exec chmod u+x '{}' +
done

%{SOURCE2} %{name} %{kmod_kernel_version} obj > source/depmod.conf

greylist=source/symbols.greylist-%{_target_cpu}
if [ -f $greylist ]; then
	cp $greylist source/symbols.greylist
else
	touch source/symbols.greylist
fi

if [ -d source/firmware ]; then
	make -C source/firmware
fi

%install
export INSTALL_MOD_PATH=$RPM_BUILD_ROOT
export INSTALL_MOD_DIR=extra/%{name}
for flavor in %flavors_to_build ; do
	make -C %{kernel_source $flavor} modules_install \
		M=$PWD/obj/$flavor/%{kmod_kbuild_dir}
	# Cleanup unnecessary kernel-generated module dependency files.
	find $INSTALL_MOD_PATH/lib/modules -iname 'modules.*' -exec rm {} \;
done

install -m 644 -D source/depmod.conf $RPM_BUILD_ROOT/etc/depmod.d/%{kmod_name}.conf
install -m 644 -D source/symbols.greylist $RPM_BUILD_ROOT/usr/share/doc/kmod-%{kmod_name}/greylist.txt

if [ -d source/firmware ]; then
	make -C source/firmware INSTALL_PATH=$RPM_BUILD_ROOT INSTALL_DIR=updates install
fi

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Tue Jul 19 2016 Petr Oros <poros@redhat.com> 1.5.10_k 2
- Build i40evf 1.5.10_k for ppc64/ppc64le arch
- Resolves: #1347173

* Wed Jun 08 2016 Petr Oros <poros@redhat.com> 1.5.10_k 1
- Update i40evf to 1.5.10_k
- Resolves: #1347173

