import re
import pytest
import logging
import functools

from tests.common.helpers.assertions import pytest_assert
from isis_helpers import DEFAULT_ISIS_INSTANCE as isis_instance
from isis_helpers import get_device_systemid
from isis_helpers import config_device_isis
from isis_helpers import add_dev_isis_attr, del_dev_isis_attr


logger = logging.getLogger(__name__)


pytestmark = [
    pytest.mark.topology('wan-com'),
]


@pytest.fixture(scope="module")
def isis_setup_teardown(isis_common_setup_teardown, request):
    target_devices = []
    selected_connections = isis_common_setup_teardown

    config_key = 'dynamic_hostname'
    config_dict = {config_key: 'false'}
    for (dut_host, _, _, _) in selected_connections:
        add_dev_isis_attr(dut_host, config_dict)
        target_devices.append(dut_host)
        config_device_isis(dut_host)

    def revert_isis_config(devices):
        for device in devices:
            del_dev_isis_attr(dut_host, [config_key])
            config_device_isis(device)

    request.addfinalizer(functools.partial(revert_isis_config, target_devices))


def test_isis_dynamic_hostname(isis_common_setup_teardown, isis_setup_teardown, nbrhosts):
    selected_connections = isis_common_setup_teardown
    (dut_host, dut_port, nbr_host, nbr_port) = selected_connections[0]

    nbr_net = get_device_systemid(nbr_host)
    isis_facts = dut_host.isis_facts()["ansible_facts"]['isis_facts']

    # The maximum length of hostname in lspid is 14, larger part will be dropped.
    if nbr_net not in isis_facts['hostname'].keys():
        pytest_assert(False, "Failed to find net {} hostname.".format(nbr_net))

    nbr_hostname = isis_facts['hostname'][nbr_net][:14]
    regex_lspid = re.compile(r'{}.\d{{2}}-\d{{2}}'.format(nbr_hostname))
    for item in isis_facts['database'][isis_instance].keys():
        if regex_lspid.match(item) is not None:
            break
    else:
        pytest_assert(False, "Failed to find hostname {} in LSPID.".format(nbr_hostname))
