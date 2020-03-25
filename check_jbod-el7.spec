Name:           check_jbod
Version:        0.0.4
%global gittag 0.0.4
Release:        1%{?dist}
Summary:        Nagios script to check the status and fault in Xyratex JBOD.

License:        Apache License 2.0
URL:            https://github.com/guilbaults/%{name}
Source0:        https://github.com/guilbaults/%{name}/archive/v%{gittag}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
Requires:       sg3_utils

%description
This tool is used to monitor Xyratex JBOD, also known as:

* Seagate/Xyratex SP-2584
* Seagate/Xyratex SP-3584
* Seagate Exos E 4U106
* Dell MD1420
These JBODs are probably also supported with some slight modifications:
* Dell MD1280
* Lenovo D3284

%prep
%autosetup -n %{name}-%{gittag}
%setup -q

%build

%install
mkdir -p %{buildroot}/usr/lib64/nagios/plugins/

sed -i -e '1i#!/usr/bin/env python' %{name}.py
install -m 0755 %{name}.py %{buildroot}/usr/lib64/nagios/plugins/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/lib64/nagios/plugins/%{name}

%changelog
* Wed Mar 25 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.5-1
- Increasing fan maximum speed threshold
* Thu Mar 19 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.4-1
- Adjusting threshold for non-idle JBODs
* Thu Mar 19 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.3-1
- Adding other models of JBODs
* Fri Jul 13 2018 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.2-1
- Fixing the shebang and the requirements
* Fri Jul 13 2018 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.1-1
- Initial release, supporting Xyratex 84 slots JBOD

