Name:           check_jbod
Version:        0.0.1
%global gittag 0.0.1
Release:        1%{?dist}
Summary:        Nagios script to check the status and fault of a 84 slots Xyratex JBOD.

License:        Apache License 2.0
URL:            https://github.com/guilbaults/%{name}
Source0:        https://github.com/guilbaults/%{name}/archive/v%{gittag}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
Requires:       sasutils
Requires:       sg3_utils

%description
This tool is used to monitor a 84 slots Xyratex JBOD, also known as:

* Seagate/Xyratex SP-2584
* Dell MD1280
* Lenovo D3284

%prep
%autosetup -n %{name}-%{gittag}
%setup -q

%build

%install
mkdir -p %{buildroot}/usr/lib64/nagios/plugins/

sed -i -e '1i#!/usr/bin/python3' %{name}.py
install -m 0755 %{name}.py %{buildroot}/usr/lib64/nagios/plugins/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/lib64/nagios/plugins/%{name}

%changelog
* Fri Jul 13 2018 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.1-1
- Initial release, supporting Xyratex 84 slots JBOD

