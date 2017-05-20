import { Routes } from "@angular/router";
import { FreeParksComponent } from "./freeparks";
import { NoOpComponent } from "./noop.component";
import { CampSitesComponent } from "./campsites";

export const ROUTES: Routes = [
    {path: '', component: NoOpComponent},
    {path: 'parks/free', component: FreeParksComponent},
    {path: 'parks/:parkName/campsites/free', component: CampSitesComponent}
];
