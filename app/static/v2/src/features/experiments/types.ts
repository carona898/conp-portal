export interface Experiment {
  id: number;
  title: string;
  description: string;
  creators: string[];
  origin: string;
  contactPerson: string;
  contactEmail: string;
  version: number;
  dateAdded: Date;
  dateUpdated: Date;
  privacy: string;
  license: string;
  keywords: string[];
  modalities: string[];
  primarySoftware: string;
  otherSoftware: string[];
  primaryFunction: string;
  otherFunctions: string[];
  doi: string;
  acknowledgements: string;
  source: string;
  views: number;
  downloads: number;
  repositoryFile: string;
  imageFile: string;
}
