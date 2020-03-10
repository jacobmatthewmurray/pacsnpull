
from pydicom.dataset import Dataset
from pynetdicom.status import code_to_category

from pynetdicom import AE
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelMove,
    PatientRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelFind)

class Mover(object):
    """docstring for DCMover"""

    def __init__(self, config):

        # Initialize the server configuration for the DC Mover

        self.client_name = config['client_name']
        self.client_port = config['client_port']

        self.host_ip = config['host_ip']
        self.host_port = config['host_port']

        # Initialize the settings for the mover

        self.query_model = config['query_model']
        self.mv_brk_cnt = config['query_break_count']

        # Start ApplicationEntity for communication with PACS

        self.ae = AE(ae_title=self.client_name)

        # Adding contexts as required

        self.ae.add_requested_context('1.2.840.10008.1.1')  # Add echo context
        if self.query_model == 'S':
            self.ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
            self.ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
        elif self.query_model == 'P':
            self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)
            self.ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        else:
            print('ERROR: Query model not recognized.')

        # Associate ApplicationEntity with PACS

        self.assoc = self.ae.associate(self.host_ip, self.host_port)
        self.currently_associated = self.assoc_check(True)

    def assoc_check(self, print_status=False):

        if self.assoc.is_established:
            if print_status:
                print('SUCCESS: associated with PACS entity')
            return True
        else:
            if print_status:
                print('FAILURE: not associated with PACS entity')
            return False

    def dictify(self, ds):

        """Turn a pydicom Dataset into a dict with keys derived from the Element keywords.

        Source: https://github.com/pydicom/pydicom/issues/319"

        Parameters
        ----------
        ds : pydicom.dataset.Dataset
            The Dataset to dictify

        Returns
        -------
        output : dict
        """
        output = dict()
        for elem in ds:
            if elem.VR != 'SQ':
                output[elem.keyword] = str(elem.value)
            else:
                output[elem.keyword] = [self.dictify(item) for item in elem]
        return output

    @staticmethod
    def make_qry_ds(qry):

        ds = Dataset()

        for i in qry:
            setattr(ds, i, qry[i])

        return ds

    def send_c_move(self, qry_dict):

        qry_ds = self.make_qry_ds(qry_dict)
        qry_response = {'status': list(), 'data': list()}
        responses = self.assoc.send_c_move(qry_ds, self.client_name, query_model=self.query_model)

        cnt = 0

        for status, ds in responses:

            status_dict = self.dictify(status)
            status_dict['status_category'] = code_to_category(status.Status)
            qry_response['status'].append(status_dict)

            if ds:
                data_dict = self.dictify(ds)
                qry_response['data'].append(data_dict)

            if cnt == self.mv_brk_cnt - 1:
                if 'NumberOfCompletedSuboperations' in qry_response['status']:
                    if sum(int(i['NumberOfCompletedSuboperations']) for i in qry_response['status']) == 0:
                        qry_response['status'].append({'Status': 'BREAK @ COUNT ={}'.format(self.mv_brk_cnt)})
                        print('ABORTING MOVE: {} STATUSES RECEIVED WITHOUT FILE MOVEMENT'.format(self.mv_brk_cnt))
                        break

            cnt += 1
        print(qry_response['status'])
        return qry_response

    def send_c_echo(self):

        status = self.assoc.send_c_echo()
        qry_response = {'status': {'code': status.Status, 'category': code_to_category(status.Status)}}

        return qry_response

    def send_c_find(self, qry_dict):

        qry_ds = self.make_qry_ds(qry_dict)
        qry_response = {'status': list(), 'data': list()}
        responses = self.assoc.send_c_find(qry_ds, query_model=self.query_model)

        for status, ds in responses:

            status_dict = {'code': status.Status, 'category': code_to_category(status.Status)}
            qry_response['status'].append(status_dict)

            if ds:
                data_dict = self.dictify(ds)
                qry_response['data'].append(data_dict)

        return qry_response


if __name__ == '__main__':
    configuration = {
            'host_ip': '127.0.0.1',
            'host_port': 4242,
            'client_name': 'STORESCP',
            'client_ip': '',
            'client_port': 2000,
            "query_model": 'S',
            "query_break_count": 10
    }

    qry = {
        'QueryRetrieveLevel': 'STUDY',
        'StudyInstanceUID': '1.2.840.113619.6.95.31.0.3.4.1.6013.13.6073688'
        # 'PatientName': '7ec8709f2db4e39ea050caf734b6a102ef2280d664d9139c565cefeb'
        # 'SeriesDescription': '*',
        # 'StudyDescription': '*',
        # 'StudyDate': '20140601-',
        # 'Modality': '*',
        # 'StudyID': '*',
        # 'AccessionNumber': '*',
        # 'PatientBirthDate': '*'
    }

    m = Mover(configuration)
    a = m.send_c_move(qry)
    m.assoc.release()

    # m = Mover(configuration)
    # m.send_c_echo()

    # m = Mover(configuration)
    # a = m.send_c_find(qry)
    # print(a)


